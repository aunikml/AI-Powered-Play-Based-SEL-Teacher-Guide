import os
import requests
import google.generativeai as genai

# --- LANGCHAIN IMPORTS (Pydantic v2 compliant) ---
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser

# --- RAG IMPORT ---
from .rag_setup import retrieve_relevant_context

# ==============================================================================
# ===         LANGCHAIN STRUCTURED OUTPUT (ENHANCED SCHEMA)                  ===
# ==============================================================================
# The descriptions for each field are now much more detailed to guide the LLM.
class TeacherGuide(BaseModel):
    """The complete, structured, and flattened data model for a teacher guide."""
    guide_title: str = Field(description="A creative, engaging, and age-appropriate title for the learning plan.")
    
    cognitive_outcomes: list[str] = Field(description="A list of 2-3 specific, observable, and measurable cognitive learning outcomes. Start each with 'The child will...'.")
    socio_emotional_outcomes: list[str] = Field(description="A list of 2-3 specific, observable, and measurable socio-emotional learning outcomes. Start each with 'The child will...'.")
    
    activity_name: str = Field(description="A clear and engaging name for the core activity.")
    activity_description: str = Field(description="A detailed, multi-sentence paragraph describing the activity. Explain what the children will do, how it directly connects to the learning outcomes, and why it is engaging and developmentally appropriate.")

    recommended_oak_content: list[str] = Field(description="Based on the context, recommend 1-2 relevant lesson titles from the provided Oak data, if applicable.")

    setup_guidance: str = Field(description="Detailed, numbered, step-by-step instructions for a teacher to set up the learning environment for this activity. Be very specific about the arrangement of materials.")
    introduction_guidance: str = Field(description="A script or detailed guide on how to introduce the activity to the children in an exciting and engaging way. Must include an interesting opening question to capture their attention.")
    during_play_guidance: str = Field(description="A comprehensive list of at least 5 distinct, open-ended questions and scaffolding prompts the teacher can use to deepen learning, encourage interaction, and support children during the activity. Include prompts for both cognitive and socio-emotional skills.")
    conclusion_guidance: str = Field(description="Step-by-step guidance on how to smoothly transition out of the activity and lead a brief, age-appropriate reflection circle. Include 2-3 specific questions to ask the children about what they did, learned, and felt.")

    materials: list[str] = Field(description="A comprehensive, bulleted list of all materials needed. For each item, add a brief parenthetical note on its purpose or a suggestion for a low-cost/recycled/natural alternative. Example: 'Large Beads (for developing fine motor skills)' or 'Cardboard Tubes (as a free alternative to building blocks)'.")

    assessment_rubric: str = Field(description="A single, detailed Markdown table that serves as an assessment matrix and rubric. The table MUST have four columns: 'Indicator', 'Emerging', 'Developing', and 'Secure'. It must contain at least 2 cognitive and 2 socio-emotional indicators derived from the learning outcomes. For each level (Emerging, Developing, Secure), provide a concrete, observable example of what a child might say or do.")

# ==============================================================================
# ===             RAG-POWERED LANGCHAIN SERVICE FUNCTION                     ===
# ==============================================================================
def generate_teacher_guide(age_cohort, subject, sub_domain, play_type_name, play_type_context, api_key):
    try:
        if not api_key or not isinstance(api_key, str):
            raise ValueError("GOOGLE_API_KEY is missing, None, or invalid.")

        # --- STEP 1: RETRIEVE RELEVANT CONTEXT ---
        query = f"Activity ideas and pedagogical principles for '{sub_domain}' within the '{subject}' domain for children aged {age_cohort}, focusing on a '{play_type_name}' play type."
        expert_context, sources = retrieve_relevant_context(query)
        if not expert_context:
             expert_context = "No specific expert context was found in the resource library. Generate the plan based on your general knowledge as an early childhood expert."
             sources = ["General Knowledge"]

        # --- STEP 2: AUGMENT & GENERATE ---
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite", temperature=0.7, google_api_key=api_key)
        structured_llm = llm.with_structured_output(schema=TeacherGuide)

        parser = PydanticOutputParser(pydantic_object=TeacherGuide)
        format_instructions = parser.get_format_instructions()

        # The prompt is updated with a stronger persona and more explicit instructions.
        prompt_template = ChatPromptTemplate.from_template(
            """
            You are an award-winning Early Childhood Education curriculum designer with 20 years of experience, specializing in play-based learning and socio-emotional development. Your task is to create an exceptionally detailed, practical, and comprehensive teacher guide. The user is a teacher who needs clear, step-by-step, actionable guidance. Your tone should be supportive, knowledgeable, and inspiring.

            You MUST return a JSON object that strictly follows the provided schema.

            **USER REQUEST:**
            *   Age Cohort: {age_cohort}
            *   Domain: {subject}
            *   Component: {sub_domain}
            *   Play Type: {play_type_name}
            *   Special Context: {play_type_context}
            
            **EXPERT-WRITTEN CONTEXT FROM YOUR ORGANIZATION'S RESOURCE LIBRARY:**
            ---
            {expert_context}
            ---

            **CRITICAL INSTRUCTIONS FOR QUALITY:**
            1.  **Prioritize the Expert Context:** You MUST base your generated activity, facilitation guidance, and outcomes on the information provided in the "EXPERT-WRITTEN CONTEXT". Do not use generic information unless no context is provided.
            2.  **Cite Your Sources:** In the 'activity_description', you MUST mention which source document(s) from the context inspired the activity. The available sources are: {sources}.
            3.  **Be Comprehensive and Step-by-Step:** Each section must be detailed. Avoid short, one-sentence answers. The facilitation guidance and setup instructions should be a clear sequence of actions.
            4.  **Be Practical:** The materials should be low-cost. The facilitation guidance should include exact, open-ended questions a teacher can use.
            5.  **Create a High-Quality Rubric:** The 'assessment_rubric' is crucial. The descriptions for 'Emerging', 'Developing', and 'Secure' MUST be concrete, observable behaviors (e.g., "Child points to one object when asked 'how many?'"), not abstract concepts (e.g., "Child understands numbers").
            6.  **Context Integration:** If the Special Context is 'Green Play' or 'Climate Vulnerability', this theme MUST be deeply and creatively woven into the activity description, materials, and facilitation guidance.

            **Output Schema:**
            {format_instructions}
            """
        )
        
        chain = prompt_template | structured_llm

        response_obj = chain.invoke({
            "age_cohort": age_cohort, "subject": subject, "sub_domain": sub_domain,
            "play_type_name": play_type_name, "play_type_context": play_type_context,
            "expert_context": expert_context,
            "sources": sources,
            "format_instructions": format_instructions,
        })
        
        return response_obj.model_dump()

    except Exception as e:
        print(f"FATAL Error in LangChain service: {e}")
        return {"error": f"Could not generate guide. The API call failed: {e}"}

# --- Deprecated helper functions (can be removed if no longer used elsewhere) ---
def get_oak_curriculum_data(age_cohort, subject):
    """This function is no longer central to the generation process but is kept for potential other uses."""
    print(f"Fetching initial Oak data for {age_cohort} years, subject: {subject}")
    return [{"title": "Counting to 10", "summary": "A lesson on number recognition."}]

def get_knowledge_base_sed_concepts():
    """This function is no longer central to the generation process but is kept for potential other uses."""
    from .models import KnowledgeBase
    try:
        concepts = KnowledgeBase.query.all()
        if not concepts: return [{"topic": "Sharing", "content": "Encourage taking turns."}]
        return [{"topic": c.topic, "content": c.content} for c in concepts]
    except Exception as e:
        print(f"Database error fetching knowledge base: {e}"); return []