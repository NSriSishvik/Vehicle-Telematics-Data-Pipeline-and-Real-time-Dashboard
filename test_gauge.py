import streamlit as st

st.title("SVG Gauge Rendering Test")

svg = """
<svg xmlns="http://www.w3.org/2000/svg"
     width="300" height="180" viewBox="0 0 300 180">
    <rect width="300" height="180" rx="12" fill="#20252b"/>
    <path d="M 40 140 A 110 110 0 0 1 260 140"
          fill="none" stroke="#777777"
          stroke-width="16" stroke-linecap="round"/>
    <text x="150" y="105" fill="white"
          font-size="30" text-anchor="middle">60</text>
    <text x="150" y="130" fill="white"
          font-size="13" text-anchor="middle">km/h</text>
</svg>
"""

