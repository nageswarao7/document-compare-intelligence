import json
import os
import logging
from typing import Dict, List, Any
import time
import math

import google.generativeai as genai
import google.api_core.exceptions

from pdf_processor import chunk_text
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Helper Function for TEXT Generation (New) ---
def call_gemini_for_text(prompt: str, model: str = "gemini-2.5-pro-preview-03-25") -> str:
    """
    Call the Google Generative AI API to get a plain text response.
    Handles basic errors and returns the text content or an empty string on failure.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        logger.error("Google API key not found for text generation.")
        return "" # Return empty on config error

    genai.configure(api_key=api_key)

    try:
        # Configure for text response (no JSON mime type)
        generation_config = {
            "temperature": 0.3, # Allow a bit more creativity for summarization
        }
        gemini_model = genai.GenerativeModel(model_name=model,
                                            generation_config=generation_config)
        logger.debug(f"Sending synthesis prompt to Gemini model: {model}. Prompt length: {len(prompt)}")
        # Add a small delay
        time.sleep(1)
        response = gemini_model.generate_content(prompt)

        if response.text:
            logger.info("Received text response from Gemini for synthesis.")
            return response.text
        else:
            # Check for blocking reasons if possible
            block_reason = response.prompt_feedback.block_reason if hasattr(response.prompt_feedback, 'block_reason') else "Unknown"
            safety_ratings = response.prompt_feedback.safety_ratings if hasattr(response.prompt_feedback, 'safety_ratings') else []
            logger.error(f"Gemini API call for text synthesis failed or returned empty. Block Reason: {block_reason}. Safety Ratings: {safety_ratings}")
            return "" # Return empty on API error/empty response

    except google.api_core.exceptions.GoogleAPIError as e:
        logger.error(f"Google API Error calling Gemini for text synthesis: {str(e)}")
        return "" # Return empty on API error
    except Exception as e:
        logger.error(f"Error calling Gemini API for text synthesis: {str(e)}")
        return "" # Return empty on other errors


# --- call_gemini_api (for JSON)  ---
def call_gemini_api(prompt: str, model: str = "gemini-2.5-pro-preview-03-25") -> str:
    """
    Call the Google Generative AI API requesting a JSON response.
    (Implementation from the previous response - unchanged)
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Google API key not found. Please set the GOOGLE_API_KEY environment variable.")

    genai.configure(api_key=api_key)

    try:
        generation_config = {
            "temperature": 0.2,
            "response_mime_type": "application/json",
        }
        gemini_model = genai.GenerativeModel(model_name=model,
                                            generation_config=generation_config)
        logger.debug(f"Sending JSON request prompt to Gemini model: {model}. Prompt length: {len(prompt)}")
        time.sleep(1)
        response = gemini_model.generate_content(prompt)

        # --- Robust Response Handling  ---
        if not response.candidates:
            block_reason = response.prompt_feedback.block_reason if hasattr(response.prompt_feedback, 'block_reason') else "Unknown"
            safety_ratings = response.prompt_feedback.safety_ratings if hasattr(response.prompt_feedback, 'safety_ratings') else []
            logger.error(f"Gemini API call failed for a chunk. Block Reason: {block_reason}. Safety Ratings: {safety_ratings}")
            return json.dumps({"error": f"API call blocked: {block_reason}", "diff_sections": [], "summary": {"additions": 0, "deletions": 0, "modifications": 0}, "detailed_summary": f"Error: API call blocked ({block_reason})"})

        if response.text and response.text.strip().startswith('{') and response.text.strip().endswith('}'):
             logger.info("Received valid JSON response structure from Gemini for chunk.")
             return response.text
        elif response.text:
             logger.warning(f"Gemini response for chunk was not valid JSON despite request: {response.text[:200]}...")
             json_start = response.text.find('{')
             json_end = response.text.rfind('}') + 1
             if json_start != -1 and json_end != -1:
                 cleaned_json = response.text[json_start:json_end]
                 try:
                     json.loads(cleaned_json)
                     logger.info("Successfully cleaned non-JSON response.")
                     return cleaned_json
                 except json.JSONDecodeError:
                     logger.error("Cleaned response is still not valid JSON.")
                     return json.dumps({"error": "Invalid JSON structure received and cleanup failed", "raw_response": response.text, "diff_sections": [], "summary": {"additions": 0, "deletions": 0, "modifications": 0}, "detailed_summary": "Error: Invalid JSON response from API."})
             else:
                 logger.error("Could not find JSON object in the Gemini response for chunk.")
                 return json.dumps({"error": "Could not extract JSON object from Gemini response", "raw_response": response.text, "diff_sections": [], "summary": {"additions": 0, "deletions": 0, "modifications": 0}, "detailed_summary": "Error: Could not extract JSON object from API response."})
        else:
            logger.error("Gemini API call returned an empty text response for chunk.")
            return json.dumps({"error": "Received empty response from Gemini API", "diff_sections": [], "summary": {"additions": 0, "deletions": 0, "modifications": 0}, "detailed_summary": "Error: Received empty response from API."})

    except google.api_core.exceptions.GoogleAPIError as e:
        logger.error(f"Google API Error calling Gemini for chunk: {str(e)}")
        return json.dumps({"error": f"Google API Error: {str(e)}", "diff_sections": [], "summary": {"additions": 0, "deletions": 0, "modifications": 0}, "detailed_summary": f"Error: Google API Error ({str(e)})"})
    except Exception as e:
        logger.error(f"Error calling Gemini API for chunk: {str(e)}")
        return json.dumps({"error": f"General Error: {str(e)}", "diff_sections": [], "summary": {"additions": 0, "deletions": 0, "modifications": 0}, "detailed_summary": f"Error: {str(e)}"})


# --- compare_chunk  ---
def compare_chunk(text1: str, text2: str, model: str = "gemini-2.5-pro-preview-03-25") -> Dict[str, Any]:
    """
    Compare two text chunks using the specified Gemini model (requests JSON).
    (Implementation from the previous response - unchanged)
    """
    prompt = f"""
You are a document comparison expert tasked with analyzing *one specific chunk* of a document.
Compare the original chunk text to the modified chunk text and identify additions, deletions, and modifications *only within this chunk*.

Original document chunk:{text1}

Modified document chunk:{text2}

Provide your analysis *only* as a single JSON object in the following format. Do not include any introductory text or markdown formatting like ```json.

{{
    "diff_sections": [
        {{"type": "unchanged", "text": "Unchanged text within the chunk"}},
        {{"type": "added", "text": "Text added within the modified chunk"}},
        {{"type": "deleted", "text": "Text deleted from the original chunk"}},
        {{"type": "modified", "text": "Modified text in this chunk", "original": "Original version in this chunk"}}
    ],
    "summary": {{
        "additions": 0, // Count for this chunk
        "deletions": 0, // Count for this chunk
        "modifications": 0 // Count for this chunk
    }},
    "detailed_summary": "A brief human-readable summary of the key changes *identified strictly within this specific chunk*"
}}
**Strictly follow the JSON format above. Do not include any other text or explanations.**
Just provide the parsable JSON object as the response.  Analyze the json object and ensure it is valid JSON. before returning it.
Focus *only* on the differences between the two provided chunks. Ensure the output is a single, valid JSON object.
"""
    try:
        response_json_str = call_gemini_api(prompt, model=model)
        logger.debug(f"Raw JSON string received for chunk comparison: {response_json_str}")
        result_json = json.loads(response_json_str)

        if "error" in result_json:
            logger.error(f"Chunk comparison failed with error: {result_json['error']}")
            return result_json
        elif "diff_sections" in result_json and "summary" in result_json and "detailed_summary" in result_json:
             logger.info("Successfully parsed valid JSON response for chunk.")
             return result_json
        else:
             logger.error(f"Parsed JSON from Gemini is missing expected keys: {result_json.keys()}")
             return {"error": "Invalid JSON structure received from Gemini", "raw_response": response_json_str, "diff_sections": [], "summary": {"additions": 0, "deletions": 0, "modifications": 0}, "detailed_summary": "Error: Invalid JSON structure received from API."}

    except json.JSONDecodeError as json_err:
        logger.error(f"Problematic response string causing JSONDecodeError: {response_json_str}")
        logger.error(f"Could not decode JSON from Gemini response string: {json_err}")
        # Create a consistent error structure
        return {"error": "Invalid response format from Gemini, failed JSON decoding",
                "raw_response": response_json_str,
                "diff_sections": [],
                "summary": {"additions": 0, "deletions": 0, "modifications": 0},
                "detailed_summary": "Error: Failed JSON decoding of API response."}
    except Exception as e:
        logger.error(f"Unexpected error in compare_chunk using Gemini: {str(e)}")
        return {"error": f"Unexpected error: {str(e)}", "diff_sections": [], "summary": {"additions": 0, "deletions": 0, "modifications": 0}, "detailed_summary": f"Unexpected Error during chunk comparison: {str(e)}"}


# --- compare_texts function ---
def compare_texts(text1: str, text2: str, model: str = "gemini-2.5-pro-preview-03-25", max_chunk_size: int = 8000) -> Dict[str, Any]:
    """
    Compare two full texts, chunking if necessary, processing all chunks,
    aggregating the results, and generating a final synthesized summary.
    """
    prompt_overhead_estimate = 1500
    effective_chunk_content_size = max_chunk_size - prompt_overhead_estimate
    if effective_chunk_content_size <= 0:
        raise ValueError("max_chunk_size is too small to accommodate the prompt overhead.")

    logger.info(f"Starting comparison. Max chunk content size: {effective_chunk_content_size} chars.")

    chunks1 = chunk_text(text1, max_chunk_size=effective_chunk_content_size)
    chunks2 = chunk_text(text2, max_chunk_size=effective_chunk_content_size)
    num_chunks1 = len(chunks1)
    num_chunks2 = len(chunks2)
    logger.info(f"Document 1 split into {num_chunks1} chunks.")
    logger.info(f"Document 2 split into {num_chunks2} chunks.")

    if not chunks1 and not chunks2:
        logger.warning("Both input texts resulted in zero chunks.")
        return {
            "diff_sections": [{"type": "unchanged", "text": ""}],
            "summary": {"additions": 0, "deletions": 0, "modifications": 0},
            "detailed_summary": "Both documents appear to be empty."
        }

    all_diff_sections: List[Dict[str, Any]] = []
    total_additions = 0
    total_deletions = 0
    total_modifications = 0
    all_chunk_summaries_raw: List[str] = [] # Store raw summaries for synthesis input
    chunk_errors: List[str] = []

    num_pairs_to_compare = min(num_chunks1, num_chunks2)
    total_chunks_to_process = max(num_chunks1, num_chunks2)

    logger.info(f"Comparing {num_pairs_to_compare} aligned chunk pairs sequentially.")

    for i in range(num_pairs_to_compare):
        logger.info(f"Processing chunk pair {i + 1} of {total_chunks_to_process}...")
        chunk1 = chunks1[i]
        chunk2 = chunks2[i]
        chunk_result = compare_chunk(chunk1, chunk2, model=model)

        if "error" not in chunk_result:
            all_diff_sections.extend(chunk_result.get("diff_sections", []))
            summary = chunk_result.get("summary", {})
            total_additions += summary.get("additions", 0)
            total_deletions += summary.get("deletions", 0)
            total_modifications += summary.get("modifications", 0)
            detailed_summary = chunk_result.get("detailed_summary")
            if detailed_summary:
                 # Store the raw summary text
                all_chunk_summaries_raw.append(detailed_summary)
        else:
            error_message = chunk_result.get("error", "Unknown error in chunk processing")
            logger.error(f"Error processing chunk pair {i + 1}: {error_message}")
            chunk_errors.append(f"Chunk {i+1}: {error_message}")
            all_diff_sections.append({
                "type": "unchanged",
                "text": f"\n\n[ERROR PROCESSING CHUNK {i+1}: {error_message}]\n\n"
            })
            all_chunk_summaries_raw.append(f"[Error processing chunk {i+1}: {error_message}]")

    # --- Handle Leftover Chunks ---
    if num_chunks2 > num_chunks1:
        logger.info(f"Processing {num_chunks2 - num_chunks1} additional chunks from Document 2 as 'added'.")
        for i in range(num_chunks1, num_chunks2):
             logger.info(f"Processing chunk {i + 1} (added)...")
             added_chunk_text = chunks2[i]
             all_diff_sections.append({"type": "added", "text": added_chunk_text})
             all_chunk_summaries_raw.append(f"Chunk {i+1}: This entire chunk was added.")
             total_additions += 1

    elif num_chunks1 > num_chunks2:
        logger.info(f"Processing {num_chunks1 - num_chunks2} additional chunks from Document 1 as 'deleted'.")
        for i in range(num_chunks2, num_chunks1):
            logger.info(f"Processing chunk {i + 1} (deleted)...")
            deleted_chunk_text = chunks1[i]
            all_diff_sections.append({"type": "deleted", "text": deleted_chunk_text})
            all_chunk_summaries_raw.append(f"Chunk {i+1}: This entire chunk was deleted.")
            total_deletions += 1

    # --- Final Synthesis Step ---
    final_detailed_summary = ""
    concatenated_chunk_summaries = "\n---\n".join(all_chunk_summaries_raw)

    # Limit the length of concatenated summaries sent for synthesis to avoid exceeding limits
    # Adjust this limit based on model and expected summary lengths
    max_synthesis_input_len = 20000 # Example limit for the synthesis input text
    if len(concatenated_chunk_summaries) > max_synthesis_input_len:
        logger.warning(f"Concatenated chunk summaries length ({len(concatenated_chunk_summaries)}) exceeds synthesis input limit ({max_synthesis_input_len}). Truncating.")
        concatenated_chunk_summaries = concatenated_chunk_summaries[:max_synthesis_input_len] + "\n... [Summaries truncated due to length]"


    if all_chunk_summaries_raw: # Only attempt synthesis if there's something to summarize
        logger.info("Attempting final summary synthesis...")
        synthesis_prompt = f"""
You are an expert analyst summarizing document changes. You have been provided with the results of a chunk-by-chunk comparison between two versions of a document.

Overall Change Counts:
- Additions: {total_additions} significant blocks/changes noted.
- Deletions: {total_deletions} significant blocks/changes noted.
- Modifications: {total_modifications} significant blocks/changes noted.

Chunk-level Summaries and Error Notes:
--- START CHUNK SUMMARIES ---
{concatenated_chunk_summaries}
--- END CHUNK SUMMARIES ---

Based *only* on the information above, generate a single, cohesive, human-readable summary of the *overall* key changes between the original and modified documents. Focus on the most significant differences.
- Do NOT mention the word "chunk" or the chunking process in your final summary.
- Synthesize the findings into a unified narrative.
- If errors were noted during chunk processing, briefly mention that some parts might be missing or inaccurate due to processing errors.
- Be concise yet informative.
"""
        try:
            synthesized_summary = call_gemini_for_text(synthesis_prompt, model=model)

            if synthesized_summary:
                final_detailed_summary = synthesized_summary
                logger.info("Successfully synthesized final summary.")
            else:
                logger.warning("Final summary synthesis failed or returned empty. Falling back to concatenated chunk summaries.")
                final_detailed_summary = "Synthesis Failed. Raw Chunk Summaries:\n---\n" + concatenated_chunk_summaries
        except Exception as synth_error:
             logger.error(f"Exception during synthesis call: {synth_error}")
             final_detailed_summary = f"Synthesis Failed ({synth_error}). Raw Chunk Summaries:\n---\n" + concatenated_chunk_summaries

    else:
        logger.info("No chunk summaries available to synthesize.")
        final_detailed_summary = "No specific changes were identified or summarized during chunk processing."

    # Prepend any chunk processing errors to the final summary for visibility
    if chunk_errors:
        error_prefix = f"**Note:** Errors occurred during the processing of {len(chunk_errors)} chunk(s). The comparison or summary below might be incomplete or inaccurate in affected areas.\nError Details:\n- " + "\n- ".join(chunk_errors) + "\n\n---\n\n"
        final_detailed_summary = error_prefix + final_detailed_summary

    logger.info("Aggregation and Synthesis complete.")

    return {
        "diff_sections": all_diff_sections,
        "summary": {
            "additions": total_additions,
            "deletions": total_deletions,
            "modifications": total_modifications,
            "chunks_processed": num_pairs_to_compare,
             "chunks_added": max(0, num_chunks2 - num_chunks1),
             "chunks_deleted": max(0, num_chunks1 - num_chunks2),
            "chunk_errors": len(chunk_errors)
        },
        "detailed_summary": final_detailed_summary # Use the synthesized or fallback summary
    }
