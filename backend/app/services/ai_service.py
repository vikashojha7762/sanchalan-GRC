"""
AI Service for OpenAI integration.
Handles embeddings and gap analysis generation.
"""
from typing import List, Optional, Dict, Any
from openai import OpenAI
from app.core.config import settings

# Initialize OpenAI client
client = OpenAI(api_key=settings.OPENAI_API_KEY)


def extract_control_requirements(control_name: str, control_description: str) -> List[str]:
    """
    Extract atomic mandatory requirements from a control description using AI.
    
    Args:
        control_name: Name of the control
        control_description: Description of the control
    
    Returns:
        List of atomic mandatory requirements
    """
    try:
        prompt = f"""Extract all atomic mandatory requirements from this control.

Control Name: {control_name}
Control Description: {control_description}

Your task:
1. Break down the control into specific, atomic mandatory requirements
2. Each requirement should be a distinct, measurable clause
3. List requirements that MUST be satisfied for compliance
4. Be specific - avoid generic statements

Example:
Control: "Access Control"
Requirements:
- User access provisioning process
- Access approval workflow
- Access revocation on termination
- Periodic access review procedures

Return ONLY a JSON array of requirement strings, no additional text:
["requirement1", "requirement2", "requirement3"]"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a compliance expert. Extract atomic mandatory requirements from control descriptions. Always return valid JSON array only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Extract JSON array
        import json
        import re
        
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            requirements = json.loads(json_match.group(0))
            if isinstance(requirements, list) and all(isinstance(r, str) for r in requirements):
                return requirements
        
        return []
        
    except Exception as e:
        print(f"[AI Service] Error extracting requirements: {str(e)}")
        return []


def decompose_control_requirements(control_text: str) -> List[str]:
    """
    Extract atomic mandatory requirements from control text using AI.
    Returns a numbered list of requirements.
    
    Args:
        control_text: Full control text (name + description)
    
    Returns:
        List of atomic mandatory requirements
    """
    try:
        prompt = f"""
Extract atomic mandatory requirements from the following ISO 27001 control.

Return as a numbered list.

CONTROL:

{control_text}
"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        
        return parse_requirements(response)
        
    except Exception as e:
        print(f"[AI Service] Error decomposing control requirements: {str(e)}")
        return []


def parse_requirements(response) -> List[str]:
    """
    Parse requirements from OpenAI response.
    Handles both numbered lists and JSON arrays.
    
    Args:
        response: OpenAI chat completion response
    
    Returns:
        List of requirement strings
    """
    try:
        response_text = response.choices[0].message.content.strip()
        requirements = []
        
        # Try to parse as numbered list (1., 2., etc. or 1), 2), etc.)
        import re
        
        # Pattern for numbered lists: "1. requirement" or "1) requirement"
        numbered_pattern = r'^\d+[\.\)]\s*(.+)$'
        lines = response_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Try numbered list format
            match = re.match(numbered_pattern, line, re.MULTILINE)
            if match:
                requirements.append(match.group(1).strip())
            # Try bullet points
            elif re.match(r'^[-•*]\s+(.+)$', line):
                req = re.sub(r'^[-•*]\s+', '', line).strip()
                if req:
                    requirements.append(req)
            # Try JSON array format
            elif line.startswith('[') or '[' in response_text:
                import json
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    try:
                        req_list = json.loads(json_match.group(0))
                        if isinstance(req_list, list):
                            return [str(r).strip() for r in req_list if r]
                    except:
                        pass
        
        # If we found requirements, return them
        if requirements:
            return requirements
        
        # Fallback: split by newlines and clean
        if response_text:
            for line in response_text.split('\n'):
                line = line.strip()
                if line and len(line) > 10:  # Filter out very short lines
                    # Remove common prefixes
                    line = re.sub(r'^[\d\.\)\-\•*]\s+', '', line).strip()
                    if line:
                        requirements.append(line)
        
        return requirements if requirements else []
        
    except Exception as e:
        print(f"[AI Service] Error parsing requirements: {str(e)}")
        return []


def get_embedding(text: str, model: str = "text-embedding-3-small") -> List[float]:
    """
    Get embedding vector for a given text using OpenAI.
    
    Args:
        text: The text to embed
        model: The embedding model to use (default: text-embedding-3-small)
    
    Returns:
        List of floats representing the embedding vector
    """
    print(f"[Embedding] Generating embedding using model: {model}")
    print(f"[Embedding] Text length: {len(text)} characters")
    
    try:
        if not text or not text.strip():
            raise Exception("Empty text provided for embedding")
        
        # Use OpenAI client to get embeddings
        print(f"[Embedding] Calling OpenAI API...")
        response = client.embeddings.create(
            model=model,
            input=text
        )
        
        embedding = response.data[0].embedding
        print(f"[Embedding] ✓ Embedding generated (dimension: {len(embedding)})")
        
        return embedding
    except Exception as e:
        import traceback
        print(f"[Embedding] ✗ ERROR generating embedding: {str(e)}")
        print(f"[Embedding] Traceback:\n{traceback.format_exc()}")
        raise Exception(f"Error generating embedding: {str(e)}")


def generate_gap_analysis(
    control_name: str,
    control_description: str,
    similar_policies: List[Dict[str, Any]],
    framework_name: Optional[str] = None,
    control_requirements: Optional[List[str]] = None,
    knowledge_base_chunks: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Generate gap analysis using OpenAI GPT.
    Analyzes control against similar policies to identify gaps.
    
    Args:
        control_name: Name of the control
        control_description: Description of the control
        similar_policies: List of similar policies with their content
        framework_name: Name of the framework (optional)
        control_requirements: List of atomic mandatory requirements (optional)
    
    Returns:
        Dictionary containing:
        - gap_identified: bool
        - severity: str (low, medium, high, critical)
        - gap_description: str
        - remediation_suggestions: List[str]
        - risk_score: float (0-100)
        - missing_requirements: List[str]
        - covered_requirements: List[str]
        - coverage_level: str (FULL|PARTIAL|NONE)
    """
    try:
        # Build context from similar policies
        policies_context = ""
        if similar_policies:
            policies_context = "\n\nSimilar Policies Found:\n"
            for idx, policy in enumerate(similar_policies[:5], 1):  # Limit to top 5
                similarity_score = policy.get('score', 0)
                policies_context += f"\n{idx}. {policy.get('title', 'Unknown')}\n"
                policies_context += f"   Similarity Score: {similarity_score:.3f}\n"
                policies_context += f"   Content: {policy.get('content', '')[:800]}...\n"
        else:
            policies_context = "\n\n⚠️ NO POLICIES FOUND: This means the control requirement is NOT covered by any existing policies in the system."
        
        # Build context from knowledge base (ground truth)
        kb_context = ""
        if knowledge_base_chunks:
            kb_context = "\n\nKNOWLEDGE BASE (Authoritative Reference):\n"
            for idx, kb_chunk in enumerate(knowledge_base_chunks[:3], 1):  # Limit to top 3
                kb_score = kb_chunk.get('score', 0)
                kb_context += f"\n{idx}. {kb_chunk.get('title', 'Unknown')}\n"
                kb_context += f"   Similarity Score: {kb_score:.3f}\n"
                kb_context += f"   Reference Text: {kb_chunk.get('text', '')[:1000]}...\n"
        else:
            kb_context = "\n\n⚠️ NO KNOWLEDGE BASE REFERENCE FOUND: No authoritative reference available for comparison."
        
        # Include control requirements if provided
        requirements_context = ""
        if control_requirements:
            requirements_context = f"\n\nMANDATORY REQUIREMENTS TO CHECK:\n" + "\n".join([f"{idx + 1}. {req}" for idx, req in enumerate(control_requirements)])
        
        # STRICT AI PROMPT - AI is EVALUATOR ONLY, NOT DECISION MAKER
        prompt = f"""You are a compliance evaluator. Your role is to EVALUATE and ANALYZE, NOT to make compliance decisions.

Your task is to EVALUATE the coverage and alignment between:
1. Control requirements
2. Existing policies
3. Knowledge Base (authoritative reference)

Control Requirement:
- Name: {control_name}
- Description: {control_description}
- Framework: {framework_name or "Not specified"}

{requirements_context}

{policies_context}

{kb_context}

EVALUATION RULES:

1. Coverage Level Assessment:
   - FULL: ALL requirements are EXPLICITLY and CLEARLY covered in policies
   - PARTIAL: Some requirements covered, some missing or not explicit
   - NONE: No requirements explicitly covered

2. Knowledge Base Alignment:
   - MATCH: Policy aligns with KB requirements (same mandatory level, same scope)
   - MISMATCH: Policy differs from KB (e.g., KB says MUST, policy says SHOULD; or KB clause omitted)
   - CONTRADICTS: Policy contradicts KB requirements

3. KB Alignment Rules:
   - If KB says MUST and policy says SHOULD → MISMATCH
   - If KB clause is omitted from policy → MISMATCH
   - If policy contradicts KB requirement → CONTRADICTS
   - FULL coverage is possible ONLY if KB alignment is MATCH

4. Evaluation Criteria:
   - Do NOT infer intent or general security statements
   - Generic language like "we follow security best practices" does NOT count as coverage
   - Must find EXPLICIT mention: specific procedures, clear processes, concrete steps

5. Which REQUIRED clauses are EXPLICITLY covered?
   - List ONLY clauses that are clearly and specifically addressed
   - Must be explicit, not inferred

6. Which REQUIRED clauses are MISSING or NOT EXPLICITLY covered?
   - Identify EVERY clause that is NOT explicitly covered
   - Be specific about what's missing

IMPORTANT: You are an EVALUATOR. Do NOT make compliance decisions. Only provide evaluation data.

Analyze and provide JSON format:
{{
    "coverage_level": "FULL|PARTIAL|NONE",
    "missing_requirements": ["requirement1", "requirement2"],
    "covered_requirements": ["requirement1"],
    "kb_alignment": "MATCH|MISMATCH|CONTRADICTS",
    "kb_reference": "Relevant KB text that was compared",
    "explanation": "Detailed explanation of coverage and KB alignment"
}}

Respond ONLY with valid JSON, no additional text:"""

        # Call OpenAI GPT with evaluator persona (NOT decision maker)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a compliance evaluator. Your role is to EVALUATE coverage and alignment, NOT to make compliance decisions. Provide accurate evaluation data: coverage_level, missing_requirements, kb_alignment, and explanation. Always respond with valid JSON only, no additional text."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,  # Very low temperature for consistent results
            max_tokens=1500
        )
        
        # Parse response
        response_text = response.choices[0].message.content.strip()
        
        # Try to extract JSON from response
        import json
        import re
        
        # Extract JSON from markdown code blocks if present
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(1)
        else:
            # Try to find JSON object
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(0)
        
        analysis = json.loads(response_text)
        
        # Validate and set defaults - AI returns EVALUATION DATA ONLY
        coverage_level = analysis.get("coverage_level", "NONE").upper()
        if coverage_level not in ["FULL", "PARTIAL", "NONE"]:
            coverage_level = "NONE"
        
        kb_alignment = analysis.get("kb_alignment", "MISMATCH").upper()
        if kb_alignment not in ["MATCH", "MISMATCH", "CONTRADICTS"]:
            # Default based on KB availability
            kb_alignment = "MISMATCH" if knowledge_base_chunks else "MISMATCH"
        
        # Return EVALUATION DATA ONLY (no compliance decision)
        return {
            "coverage_level": coverage_level,
            "missing_requirements": analysis.get("missing_requirements", []),
            "covered_requirements": analysis.get("covered_requirements", []),
            "kb_alignment": kb_alignment,
            "kb_reference": analysis.get("kb_reference", ""),
            "explanation": analysis.get("explanation", "No explanation provided")
        }
        
    except json.JSONDecodeError as e:
        # Fallback: Return default evaluation data
        print(f"[AI Service] ⚠️ JSON parsing failed: {str(e)}")
        return {
            "coverage_level": "NONE",
            "missing_requirements": [],
            "covered_requirements": [],
            "kb_alignment": "MISMATCH",
            "kb_reference": "",
            "explanation": f"Unable to parse AI response. Control: {control_name}. JSON parsing error: {str(e)}"
        }
    except Exception as e:
        # Fallback: Return default evaluation data
        print(f"[AI Service] ⚠️ Error in gap analysis: {str(e)}")
        return {
            "coverage_level": "NONE",
            "missing_requirements": [],
            "covered_requirements": [],
            "kb_alignment": "MISMATCH",
            "kb_reference": "",
            "explanation": f"Error analyzing control: {str(e)}"
        }
