# PUBG Console Arena - PS5 & Xbox Series

A complete tournament platform for PUBG on PlayStation 5 and Xbox Series X|S with automated stat tracking and PayPal payouts.

[![Deploy to Render](https://render.com/images/deploy-to-render.svg)](https://render.com/deploy)

## 🚀 Easy Hosting Guide

### 1. Static Preview (GitHub Pages)
This repository is pre-configured for GitHub Pages. You can host a professional landing page for your users for free directly from the root of your repo.

- **How to enable**:
  1. Push this code to your GitHub repository.
  2. Go to **Settings** > **Pages**.
  3. Under **Build and deployment** > **Branch**, select `main` and **(root)**.
  4. Click **Save**. Your site will be live at `https://yourusername.github.io/yourrepo/`.

### 2. Full Application (Python Backend)
To use the registration system, stat tracking, and PayPal payouts, you need to host the Python code.

- **Recommended Platforms**:
  - **Render**: Connect repo, use `gunicorn app:app`.
  - **Vercel**: Pre-configured with `vercel.json`. Simply import the repo into Vercel.
  - **Railway**: Automatic detection of `Procfile`.

---

## 🛠 Features
- **Stat Tracking**: Automatic retrieval of kills, wins, and placement via the **PUBG API**.
- **Console Integration**: Dedicated support for Xbox Gamertags and PSN IDs.
- **PayPal Payouts**: Automated prize distribution to winners.
- **Free Funding**: Built-in logic for sponsorship-funded prize pools.

## 🔑 Setup & Configuration
1. **PUBG API**: Get your key at [developer.pubg.com](https://developer.pubg.com/).
2. **PayPal**: Create a developer account at [developer.paypal.com](https://developer.paypal.com/) and enable "Payouts".
3. **Database**: Uses SQLite by default. For production, connect a PostgreSQL database via the `DATABASE_URL` environment variable.

## 📂 Project Structure
- `/docs`: Static site for GitHub Pages.
- `/templates`: Dynamic Flask templates.
- `app.py`: Backend logic & API coordination.
- `models.py`: Database schema.
- `pubg_api.py`: PUBG API wrapper.

## 📜 License
MIT License. Free to use and modify for your own tournaments!
