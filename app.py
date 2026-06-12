import streamlit as st

st.title("Simple Streamlit App")

name = st.text_input("Enter your name")

if name:
    st.write(f"Hello, {name}! Welcome to the app.")

age = st.slider("Select your age", 0, 100, 25)
st.write(f"Selected age: {age}")

if st.button("Celebrate!"):
    st.balloons()
    st.success("🎉 Celebration time!")