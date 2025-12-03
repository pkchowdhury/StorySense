"""
Streamlit UI for Human Evaluation of Story Refinements
Run with: streamlit run human_rating_app.py
"""

import streamlit as st
import json
import pandas as pd
from pathlib import Path

# Page config
st.set_page_config(
    page_title="StorySense App",
    page_icon="📝",
    layout="wide"
)

class RatingApp:
    def __init__(self):
        self.init_session_state()
    
    def init_session_state(self):
        """Initialize session state variables"""
        if 'current_idx' not in st.session_state:
            st.session_state.current_idx = 0
        if 'ratings' not in st.session_state:
            st.session_state.ratings = {}
        if 'stories_loaded' not in st.session_state:
            st.session_state.stories_loaded = False
    
    def load_evaluation_data(self, filepath: str):
        """Load stories and outputs for evaluation"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            st.session_state.evaluation_data = data
            st.session_state.stories_loaded = True
            return True
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return False
    
    def render_story_comparison(self, story_data):
        """Render side-by-side comparison of Arm A and Arm B outputs"""
        
        st.markdown("### Original Story")
        with st.expander("View Original", expanded=False):
            st.markdown(f"**Title:** {story_data['original']['title']}")
            st.markdown(f"**Description:** {story_data['original']['description']}")
            st.markdown(f"**ACs:**")
            for ac in story_data['original']['ACs']:
                st.markdown(f"- {ac}")
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🅰️ Output A")
            self.render_output(story_data['arm_a'])
        
        with col2:
            st.markdown("### 🅱️ Output B")
            self.render_output(story_data['arm_b'])
    
    def render_output(self, output_data):
        """Render a single output"""
        
        story = output_data.get('story', {})
        
        st.markdown(f"**Title:** {story.get('title', 'N/A')}")
        st.markdown(f"**Description:** {story.get('description', 'N/A')}")
        
        st.markdown("**Acceptance Criteria:**")
        for ac in output_data.get('ACs', []):
            st.markdown(f"- {ac}")
        
        if output_data.get('risks'):
            with st.expander("Risks", expanded=False):
                for risk in output_data['risks']:
                    st.markdown(f"- {risk}")
        
        if output_data.get('openQuestions'):
            with st.expander("Open Questions", expanded=False):
                for q in output_data['openQuestions']:
                    st.markdown(f"- {q}")
        
        # Show compliance findings for Arm B
        if output_data.get('compliance_findings'):
            with st.expander("Compliance Findings", expanded=False):
                for finding in output_data['compliance_findings']:
                    status_icon = "✅" if finding['status'] == 'pass' else "❌"
                    st.markdown(f"{status_icon} **{finding['clauseId']}**: {finding['rationale']}")
    
    def render_rating_form(self, story_id: str):
        """Render rating form for current story"""
        
        st.markdown("---")
        st.markdown("## 📊 Rate Both Outputs")
        
        # Create tabs for Arm A and Arm B ratings
        tab_a, tab_b = st.tabs(["Rate Output A", "Rate Output B"])
        
        ratings = {}
        
        with tab_a:
            ratings['arm_a'] = self.render_invest_ratings("A")
            ratings['arm_a_quality'] = self.render_quality_ratings("A")
            ratings['arm_a_preference'] = st.slider(
                "Overall Preference for A (1=Poor, 5=Excellent)",
                1, 5, 3, key=f"pref_a_{story_id}"
            )
        
        with tab_b:
            ratings['arm_b'] = self.render_invest_ratings("B")
            ratings['arm_b_quality'] = self.render_quality_ratings("B")
            ratings['arm_b_preference'] = st.slider(
                "Overall Preference for B (1=Poor, 5=Excellent)",
                1, 5, 3, key=f"pref_b_{story_id}"
            )
        
        # Comments
        st.markdown("### 💬 Comments")
        ratings['comments'] = st.text_area(
            "Additional observations or notes",
            key=f"comments_{story_id}"
        )
        
        # Which is better?
        st.markdown("### 🏆 Final Verdict")
        ratings['winner'] = st.radio(
            "Which output is better overall?",
            ["A is better", "B is better", "Both are equal", "Both are poor"],
            key=f"winner_{story_id}"
        )
        
        return ratings
    
    def render_invest_ratings(self, arm: str) -> dict:
        """Render INVEST facet ratings"""
        
        st.markdown(f"#### INVEST Ratings - Arm {arm}")
        
        facets = {
            "Independent": "Story is self-contained, no dependencies",
            "Negotiable": "Leaves room for discussion on implementation",
            "Valuable": "Clear stakeholder value",
            "Estimable": "Can be estimated by the team",
            "Small": "Fits in one iteration",
            "Testable": "Has verifiable acceptance criteria"
        }
        
        ratings = {}
        
        col1, col2 = st.columns(2)
        
        for idx, (facet, description) in enumerate(facets.items()):
            col = col1 if idx % 2 == 0 else col2
            with col:
                ratings[facet] = st.slider(
                    f"{facet}",
                    1, 5, 3,
                    help=description,
                    key=f"invest_{facet}_{arm}_{st.session_state.current_idx}"
                )
        
        return ratings
    
    def render_quality_ratings(self, arm: str) -> dict:
        """Render quality ratings"""
        
        st.markdown(f"#### Quality Ratings - Arm {arm}")
        
        ratings = {}
        
        ratings['readability'] = st.slider(
            "Readability (1=Hard to read, 5=Very clear)",
            1, 5, 3,
            key=f"read_{arm}_{st.session_state.current_idx}"
        )
        
        ratings['understandability'] = st.slider(
            "Understandability (1=Confusing, 5=Very clear)",
            1, 5, 3,
            key=f"understand_{arm}_{st.session_state.current_idx}"
        )
        
        ratings['completeness'] = st.slider(
            "Completeness (1=Missing info, 5=Complete)",
            1, 5, 3,
            key=f"complete_{arm}_{st.session_state.current_idx}"
        )
        
        return ratings
    
    def save_ratings(self, ratings: dict, story_id: str):
        """Save ratings to session state"""
        st.session_state.ratings[story_id] = ratings
    
    def export_ratings(self):
        """Export all ratings to JSON"""
        output = {
            "metadata": {
                "total_rated": len(st.session_state.ratings),
                "rater": st.session_state.get('rater_name', 'anonymous')
            },
            "ratings": st.session_state.ratings
        }
        
        return json.dumps(output, indent=2)
    
    def run(self):
        """Main app logic"""
        
        st.title("📝 User Story Quality Evaluation")
        st.markdown("Compare and rate story refinements from two different approaches")
        
        # Sidebar
        with st.sidebar:
            st.markdown("### ⚙️ Configuration")
            
            rater_name = st.text_input("Your Name", key="rater_name")
            
            st.markdown("---")
            st.markdown("### 📂 Load Data")
            
            uploaded_file = st.file_uploader(
                "Upload evaluation data (JSON)",
                type=['json']
            )
            
            if uploaded_file:
                data = json.load(uploaded_file)
                st.session_state.evaluation_data = data
                st.session_state.stories_loaded = True
                st.success("Data loaded!")
            
            if st.session_state.stories_loaded:
                st.markdown("---")
                st.markdown("### 📊 Progress")
                total = len(st.session_state.evaluation_data.get('stories', []))
                rated = len(st.session_state.ratings)
                st.progress(rated / total if total > 0 else 0)
                st.markdown(f"**{rated} / {total}** stories rated")
                
                st.markdown("---")
                if st.button("⬇️ Export Ratings"):
                    ratings_json = self.export_ratings()
                    st.download_button(
                        "Download Ratings",
                        ratings_json,
                        "ratings.json",
                        "application/json"
                    )
        
        # Main content
        if not st.session_state.stories_loaded:
            st.info("👆 Please upload evaluation data to begin")
            
            # Show example data format
            with st.expander("Expected Data Format"):
                st.json({
                    "stories": [
                        {
                            "story_id": "STORY-001",
                            "original": {
                                "title": "...",
                                "description": "...",
                                "ACs": ["..."]
                            },
                            "arm_a": {
                                "story": {"title": "...", "description": "..."},
                                "ACs": ["..."],
                                "risks": ["..."]
                            },
                            "arm_b": {
                                "story": {"title": "...", "description": "..."},
                                "ACs": ["..."],
                                "compliance_findings": [{"clauseId": "...", "status": "..."}]
                            }
                        }
                    ]
                })
        else:
            stories = st.session_state.evaluation_data.get('stories', [])
            
            if not stories:
                st.error("No stories found in data")
                return
            
            # Navigation
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col1:
                if st.button("⬅️ Previous") and st.session_state.current_idx > 0:
                    st.session_state.current_idx -= 1
                    st.rerun()
            
            with col2:
                st.markdown(f"### Story {st.session_state.current_idx + 1} of {len(stories)}")
            
            with col3:
                if st.button("Next ➡️") and st.session_state.current_idx < len(stories) - 1:
                    st.session_state.current_idx += 1
                    st.rerun()
            
            # Current story
            current_story = stories[st.session_state.current_idx]
            story_id = current_story['story_id']
            
            st.markdown(f"**Story ID:** `{story_id}`")
            
            # Render comparison
            self.render_story_comparison(current_story)
            
            # Render rating form
            ratings = self.render_rating_form(story_id)
            
            # Save button
            if st.button("💾 Save Ratings", type="primary"):
                self.save_ratings(ratings, story_id)
                st.success(f"✅ Ratings saved for {story_id}")
                
                # Auto-advance
                if st.session_state.current_idx < len(stories) - 1:
                    st.session_state.current_idx += 1
                    st.rerun()

# Run app
if __name__ == "__main__":
    app = RatingApp()
    app.run()