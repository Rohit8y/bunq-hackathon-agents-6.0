import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import asyncio
# Adjust the path to import from the parent directory

from v1_agents import main  # main() returns structured data

# --- Streamlit UI ---
st.set_page_config(page_title="🌍 Sustainable Spending Dashboard", layout="wide")

st.title("🌱 Welcome to Your Sustainable Spending Dashboard")
st.markdown(
    "Track your finances, understand your carbon impact, and take meaningful climate action. "
    "This dashboard helps you reflect on your spending habits and how they translate into CO₂ emissions — "
    "with friendly encouragement and clear visual insights. 💚"
)


# Load and run agents
with st.spinner("Fetching your financial & sustainability insights..."):
    result = asyncio.run(main())

# Unpack results
habits_output = result["habits_output"]
user_spending = result["user_spending"]
co2_output = result["co2_output"]
offset_amount = result["offset_amount"]
green_balance = result["green_balance"]
motivation_text = result["motivation"]

# 🧾 Spending Summary
st.header("📊 Spending Summary")
st.markdown(f"**🧠 Summary:** {habits_output.spending_summary_text}")

# 🌱 Carbon Footprint Summary
st.header("🌿 Carbon Impact Summary")
col1, col2, col3 = st.columns(3)
col1.metric("🌍 Total CO₂ Emitted", f"{co2_output.total_co2:.2f} kg")
col2.metric("📉 CO₂ per € Spent", f"{co2_output.co2_per_euro:.3f} kg/€")
zone_color = "green" if co2_output.zone == "Green" else "orange" if co2_output.zone == "Yellow" else "red"
col3.markdown(f"### 🔵 Sustainability Zone")
col3.markdown(f"<span style='color:{zone_color}; font-size: 1.5em; font-weight: bold'>{co2_output.zone}</span>", unsafe_allow_html=True)

# 📊 Category Distribution
st.header("🧩 Spending Breakdown")
col1, col2 = st.columns([2, 1])

with col1:
    df_dist = pd.DataFrame([vars(c) for c in habits_output.category_percentage_distribution])
    fig1, ax1 = plt.subplots()
    ax1.pie(df_dist['percentage'], labels=df_dist['category'], autopct='%1.1f%%', startangle=90)
    ax1.set_title("Spending Distribution by Category")
    ax1.axis('equal')
    st.pyplot(fig1)

with col2:
    st.markdown("**Category % Breakdown**")
    st.dataframe(df_dist, use_container_width=True)

# 💳 Raw Spending Table (Expandable)
with st.expander("📂 View Raw Spending Details"):
    raw_spending_df = pd.DataFrame(user_spending.items(), columns=["Category", "Amount (€)"])
    st.dataframe(raw_spending_df, use_container_width=True)



# 💸 Offset Section
st.header("💰 CO₂ Offset & Climate Action")
col1, col2 = st.columns(2)
col1.metric("✅ Offset Transferred", f"{offset_amount:.2f} €")
col2.metric("🏦 Green Account Balance", f"{green_balance:.2f} €")

# 🌟 Motivation Insight
st.header("🌟 Motivation Insight")
st.success(motivation_text)

import numpy as np

# 🏆 Sustainability Leaderboard
st.header("🏆 Sustainability Leaderboard")

# Real user values
total_spent = raw_spending_df["Amount (€)"].sum()
ratio = round(offset_amount / total_spent, 3) if total_spent != 0 else 0

real_user = {
    "User": "John Peter Clarkson ⭐",
    "Total Spent (€)": round(total_spent, 2),
    "CO₂ Emitted (kg)": co2_output.total_co2,
    "Offset Contributed (€)": offset_amount,
    "Ratio Saved/Spent": ratio
}

# Generate fake users
import numpy as np
fake_users = []
for name in ["Alice", "Ben", "Clara", "David", "Ella"]:
    spent = round(np.random.uniform(200, 1000), 2)
    offset = round(np.random.uniform(5, 100), 2)
    fake_users.append({
        "User": name,
        "Total Spent (€)": spent,
        "CO₂ Emitted (kg)": round(spent * np.random.uniform(0.3, 0.7), 2),
        "Offset Contributed (€)": offset,
        "Ratio Saved/Spent": round(offset / spent, 3)
    })

# ✅ Combine, sort, then set rank index
leaderboard_df = pd.DataFrame([real_user] + fake_users)
leaderboard_df = leaderboard_df.sort_values(by="Ratio Saved/Spent", ascending=False).reset_index(drop=True)
leaderboard_df.index = leaderboard_df.index + 1  # Start rank from 1
leaderboard_df.index.name = "Rank"

# 🎨 Highlight John’s row
def highlight_user(row):
    if "Clarkson" in row["User"]:
        return ['background-color: #FFE5B4; color: black; font-weight: bold'] * len(row)
    else:
        return [''] * len(row)

# Display styled leaderboard
styled_leaderboard = leaderboard_df.style\
    .apply(highlight_user, axis=1)\
    .format({
        "Total Spent (€)": "€{:.2f}",
        "Offset Contributed (€)": "€{:.2f}",
        "Ratio Saved/Spent": "{:.3f}"
    })

st.dataframe(styled_leaderboard, use_container_width=True)


