# PrivacyGuard: Educational App Privacy Analyzer

![PrivacyGuard Banner](public/icons.svg)

> **Final Year Research Project**: Automated Privacy Risk Analysis and Visualization Platform for Free Educational Android Applications.

PrivacyGuard is a React-based analysis dashboard designed to help parents, educators, and researchers evaluate the privacy risks associated with children's educational Android apps. It visualizes data from static and dynamic APK analysis, highlighting dangerous permissions, third-party trackers, network security flaws, and Data Safety disclosure mismatches.

## 🚀 Features

- **Risk Dashboard**: High-level overview of analyzed applications with a responsive pie chart of risk distributions.
- **Dynamic Search & Filter**: Easily filter the database of analyzed apps by name, developer, or risk severity (Low, Medium, High).
- **Deep-Dive App Analysis**: 
  - **Risk Radar Chart**: Multi-dimensional scoring across Permissions, Trackers, Network, Storage, and Child Safety.
  - **Disclosure Mismatch Detection**: Compares actual app behavior against Google Play Store Data Safety claims, flagging policy violations.
  - **Tracker & Network Analysis**: Identifies third-party SDKs (AdMob, Facebook, etc.) and highlights unencrypted (HTTP) endpoints.
  - **Plain-Language Risk Factors**: Translates technical findings into understandable warnings for non-technical users.
- **Side-by-Side Comparison**: Compare multiple applications across key privacy metrics simultaneously.

## 🛠️ Tech Stack

- **Core**: React 19, Vite 8, React Router 7
- **Styling**: Tailwind CSS 4 (with custom glassmorphism and modern glow aesthetics)
- **Data Visualization**: Recharts
- **Icons**: Lucide React
- **Code Quality**: ESLint

## 📊 Research Context

Children's educational apps often contain behavioral trackers and collect data without verifiable parental consent, violating regulations like COPPA. This platform serves as the visualization frontend for an automated APK analysis pipeline. 

The risk score (0-100) is calculated based on:
1. Number of dangerous permissions requested vs. actively used.
2. Presence and severity of third-party advertising and analytics SDKs.
3. Network transmission security (HTTPS vs HTTP).
4. Accuracy of developer-provided data safety disclosures.

## 💻 Installation & Usage

1. **Clone the repository**
   ```bash
   git clone https://github.com/NimeshWickram/Automated-Privacy-Risk-Analysis-and-Visualization-Platform.git
   cd research
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start the development server**
   ```bash
   npm run dev
   ```

4. **Build for production**
   ```bash
   npm run build
   ```

## 🔮 Future Enhancements

- **PDF Report Generation**: Export detailed analysis reports for sharing.
- **Live APK Upload**: Interface for users to upload an APK and trigger the backend analysis pipeline in real-time.
- **Methodology Documentation Page**: In-app documentation detailing the exact heuristics used for risk scoring.
- **Trend Analysis**: Statistical visualizations showing how app privacy evolves over time.

---
*Developed for research purposes.*
