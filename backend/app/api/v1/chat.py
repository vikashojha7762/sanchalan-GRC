from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from openai import OpenAI
from typing import Literal
import re
from app.db import get_db
from app.models import User
from app.api.v1.auth import get_current_user
from app.schemas.chat import ChatQuery, ChatResponse
from app.services.pinecone_service import query_similar_policies
from app.services.ai_service import get_embedding
from app.core.config import settings

router = APIRouter()

# Initialize OpenAI client for chat
client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Chat-specific similarity threshold (lower than gap analysis for more lenient matching)
CHAT_SIMILARITY_THRESHOLD = 0.60


def detect_intent(query: str) -> Literal["greeting", "small_talk", "general_knowledge", "knowledge_question"]:
    """
    FIX 1: Detect user intent before querying knowledge base.
    
    Args:
        query: User's query text
    
    Returns:
        Intent type: "greeting", "small_talk", "general_knowledge", or "knowledge_question"
    """
    query_lower = query.lower().strip()
    
    # Greeting patterns
    greeting_patterns = [
        r'^(hi|hello|hey|greetings|good morning|good afternoon|good evening)',
        r'^(hi|hello|hey)\s*$',
        r'^(hi|hello|hey)\s+there',
        r'^howdy'
    ]
    
    for pattern in greeting_patterns:
        if re.match(pattern, query_lower):
            return "greeting"
    
    # Small talk patterns
    small_talk_patterns = [
        r'^(how are you|how\'?s it going|what\'?s up|how do you do)',
        r'^(thanks|thank you|thx)',
        r'^(bye|goodbye|see you|farewell)',
        r'^(yes|no|ok|okay|sure|alright)',
        r'^(what can you do|what are you|who are you)',
        r'^(help|help me)'
    ]
    
    for pattern in small_talk_patterns:
        if re.match(pattern, query_lower):
            return "small_talk"
    
    # General knowledge questions (can be answered without specific policies)
    # These are questions about concepts, definitions, or general topics
    general_knowledge_patterns = [
        r'^(what is|what\'?s|explain|tell me about|define|describe|what does|what do you know about)\s+',
        r'^(how does|how do|how is|how are)\s+',
        r'^(what are|what\'?re)\s+',
        r'^(can you explain|can you tell me|can you describe)\s+',
    ]
    
    for pattern in general_knowledge_patterns:
        if re.match(pattern, query_lower):
            return "general_knowledge"
    
    # Default to knowledge question (requires KB search for specific policies/controls)
    return "knowledge_question"


@router.post("/query", response_model=ChatResponse)
async def chat_query(
    chat_query: ChatQuery,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Chat query endpoint using RAG (Retrieval Augmented Generation).
    FIX: Added intent detection to skip KB search for greetings/small talk.
    Searches Pinecone for relevant APPROVED policies and uses OpenAI to generate response.
    """
    try:
        # Validate query
        if not chat_query.query or not chat_query.query.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query cannot be empty"
            )
        
        user_query = chat_query.query.strip()
        
        # FIX 1: Detect intent before querying knowledge base
        intent = detect_intent(user_query)
        print(f"[Chat] Detected intent: {intent} for query: {user_query[:50]}...")
        
        # FIX 2: Handle greetings and small talk without KB search
        if intent == "greeting":
            return ChatResponse(
                answer="Hello! I'm your AI GRC assistant. I can help you with questions about policies, controls, compliance frameworks, and gap analysis. What would you like to know?",
                sources=None,
                confidence=None
            )
        
        if intent == "small_talk":
            # Generate conversational response for small talk
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a friendly AI assistant for a GRC platform. Respond naturally to small talk and casual conversation. Keep responses brief and friendly."
                        },
                        {
                            "role": "user",
                            "content": user_query
                        }
                    ],
                    temperature=0.7,
                    max_tokens=200
                )
                answer = response.choices[0].message.content.strip()
            except Exception as e:
                answer = "I'm here to help! Feel free to ask me about policies, controls, or compliance questions."
            
            return ChatResponse(
                answer=answer,
                sources=None,
                confidence=None
            )
        
        # FIX: Handle general knowledge questions (can answer without specific policies)
        # These questions about concepts/definitions can be answered with general knowledge
        # but we'll still try KB first, then fall back to general knowledge if no results
        is_general_knowledge = (intent == "general_knowledge")
        
        # FIX 3 & 4: Query KB for both general knowledge and specific knowledge questions
        # FIX 4: Use lower similarity threshold for chat (0.60 vs 0.72 for gap analysis)
        similar_policies = []
        try:
            # FIX 3: Build filter with company_id and status=approved
            # Note: Status is stored as lowercase enum value (e.g., "approved")
            filter_metadata = {}
            if current_user.company_id:
                filter_metadata["company_id"] = current_user.company_id
            # Filter for approved policies only (status enum value is lowercase "approved")
            filter_metadata["status"] = "approved"
            
            print(f"[Chat] Querying KB with filters: company_id={current_user.company_id}, status=approved")
            
            similar_policies = query_similar_policies(
                query_text=user_query,
                top_k=5,
                filter_metadata=filter_metadata,
                similarity_threshold=CHAT_SIMILARITY_THRESHOLD  # FIX 4: Lower threshold for chat
            )
            print(f"[Chat] Found {len(similar_policies)} similar policies (threshold: {CHAT_SIMILARITY_THRESHOLD})")
        except Exception as pinecone_error:
            # If Pinecone fails, log but continue without context
            import traceback
            print(f"[Chat] Warning: Pinecone query failed: {str(pinecone_error)}")
            print(f"[Chat] Traceback: {traceback.format_exc()}")
            # Continue without similar policies - will use fallback
            similar_policies = []
        
        # Step 2: Build context from retrieved policies
        context = ""
        sources = []
        
        if similar_policies and len(similar_policies) > 0:
            context = "Relevant Policies and Information:\n\n"
            for idx, policy in enumerate(similar_policies, 1):
                policy_title = policy.get('title', 'Unknown')
                policy_content = policy.get('content', '')[:800] if policy.get('content') else ''
                policy_score = policy.get('score', 0)
                
                context += f"{idx}. {policy_title}\n"
                if policy_content:
                    context += f"   Content: {policy_content}\n"
                context += f"   Relevance Score: {policy_score:.2f}\n\n"
                
                sources.append({
                    "policy_id": policy.get("policy_id"),
                    "title": policy_title,
                    "score": float(policy_score) if policy_score else 0.0,
                    "metadata": policy.get("metadata", {})
                })
        
        # FIX 5: Improved fallback behavior based on intent
        if not similar_policies or len(similar_policies) == 0:
            # No KB results found
            if is_general_knowledge:
                # For general knowledge questions (what is X, explain X), provide general answer
                # even without specific policies in KB
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {
                                "role": "system",
                                "content": "You are an AI assistant for a GRC (Governance, Risk, and Compliance) platform. Answer general knowledge questions about GRC concepts, frameworks, compliance, risk management, and governance. Provide clear, informative explanations. If the question is about a general concept, explain it even if you don't have specific policy references."
                            },
                            {
                                "role": "user",
                                "content": user_query
                            }
                        ],
                        temperature=0.7,
                        max_tokens=500
                    )
                    answer = response.choices[0].message.content.strip()
                except Exception as e:
                    answer = "I apologize, but I encountered an error. Please try rephrasing your question."
                
                return ChatResponse(
                    answer=answer,
                    sources=None,
                    confidence=None
                )
            else:
                # For specific knowledge questions without KB results, ask clarifying question
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {
                                "role": "system",
                                "content": "You are an AI assistant for a GRC platform. When you don't have specific information in the knowledge base, politely ask the user to clarify their question or provide more details. Do NOT provide generic GRC explanations. Keep responses brief and helpful."
                            },
                            {
                                "role": "user",
                                "content": f"User asked: {user_query}\n\nI couldn't find specific policies in the knowledge base. Generate a helpful response that asks for clarification without providing generic GRC information."
                            }
                        ],
                        temperature=0.7,
                        max_tokens=150
                    )
                    answer = response.choices[0].message.content.strip()
                except Exception as e:
                    answer = "I couldn't find specific information about that in our knowledge base. Could you provide more details or rephrase your question?"
                
                return ChatResponse(
                    answer=answer,
                    sources=None,
                    confidence=None
                )
        
        # Step 3: Generate response using OpenAI with RAG context (only if KB results found)
        system_prompt = """You are an AI assistant for a Governance, Risk, and Compliance (GRC) platform.
Your role is to help users understand policies, controls, frameworks, and compliance requirements.
Use the provided context from the knowledge base to answer questions accurately.
Always cite sources when referencing specific policies.
If the context doesn't fully answer the question, acknowledge what you can answer and what might need clarification."""
        
        user_prompt = f"""Context from Knowledge Base:
{context}

User Question: {user_query}

Please provide a helpful and accurate answer based on the context above. If you reference specific policies, mention them by title."""
        
        # Generate response using OpenAI
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content.strip()
            
            if not answer:
                answer = "I apologize, but I couldn't generate a response. Please try rephrasing your question."
                
        except Exception as openai_error:
            print(f"[Chat] OpenAI API error: {str(openai_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating AI response: {str(openai_error)}"
            )
        
        # Calculate confidence based on similarity scores
        confidence = None
        if similar_policies and len(similar_policies) > 0:
            scores = [p.get("score", 0) for p in similar_policies if p.get("score")]
            if scores:
                avg_score = sum(scores) / len(scores)
                confidence = round(avg_score * 100, 2)  # Convert to percentage
        
        return ChatResponse(
            answer=answer,
            sources=sources if sources else None,
            confidence=confidence
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log the full error for debugging
        import traceback
        error_trace = traceback.format_exc()
        print(f"[Chat] Chat query error: {str(e)}")
        print(f"[Chat] Traceback: {error_trace}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat query: {str(e)}"
        )
