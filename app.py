import streamlit as st
import tempfile
import os
from pdf_processor import extract_text_from_pdf
from llm_comparer import compare_texts
from visualizer import generate_diff_html

def main():
    st.set_page_config(page_title="Document Compare Intelligence", layout="wide")
    
    st.markdown("<h1 style='text-align: center;'>Document Compare Intelligence</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Upload your documents to instantly identify and visualize changes between versions.</p>", unsafe_allow_html=True)
    # File upload section
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Original Document")
        pdf1 = st.file_uploader("Upload the original PDF", type=['pdf'], key="pdf1")
    
    with col2:
        st.subheader("Modified Document")
        pdf2 = st.file_uploader("Upload the modified PDF", type=['pdf'], key="pdf2")
    
    if pdf1 and pdf2:
        # Create a button to trigger the comparison
        if st.button("Compare Documents"):
            with st.spinner("Processing PDFs..."):
                # Create temporary files
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp1:
                    tmp1.write(pdf1.getvalue())
                    tmp1_path = tmp1.name
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp2:
                    tmp2.write(pdf2.getvalue())
                    tmp2_path = tmp2.name
                
                # Extract text from PDFs
                st.info("Extracting text from PDFs...")
                text1 = extract_text_from_pdf(tmp1_path)
                text2 = extract_text_from_pdf(tmp2_path)
                
                # Clean up temporary files
                os.unlink(tmp1_path)
                os.unlink(tmp2_path)
                
                # Compare texts using LLM
                st.info("Analyzing differences with Gemini...")
                comparison_result = compare_texts(text1, text2) # Model defaults to gemini-1.5-flash

                # --- Add more robust error checking ---
                if "error" in comparison_result:
                    st.error(f"Comparison failed: {comparison_result['error']}")
                    # Optionally display raw response if available and useful for debugging
                    if "raw_response" in comparison_result:
                        st.expander("Show Raw Response (for debugging)").text(comparison_result["raw_response"])
                else:
                    # Display results (existing code)
                    st.success("Comparison completed!")

                    # Check if summary exists before accessing keys
                    if comparison_result.get("summary"):
                        st.subheader("Summary of Changes")
                        st.write(f"Additions: {comparison_result['summary'].get('additions', 'N/A')}")
                        st.write(f"Deletions: {comparison_result['summary'].get('deletions', 'N/A')}")
                        st.write(f"Modifications: {comparison_result['summary'].get('modifications', 'N/A')}")
                    else:
                        st.warning("Summary information not available in the response.")

                    # Check if detailed summary exists
                    if comparison_result.get("detailed_summary"):
                        st.subheader("Change Analysis")
                        st.write(comparison_result['detailed_summary'])
                    else:
                        st.warning("Detailed summary not available in the response.")

                    # Check if diff sections exist
                    if comparison_result.get("diff_sections"):
                        st.subheader("Visualized Differences")
                        diff_html = generate_diff_html(comparison_result['diff_sections'])
                        st.components.v1.html(diff_html, height=800, scrolling=True)
                    else:
                        st.warning("Difference sections not available for visualization.")
        
if __name__ == "__main__":
    main()