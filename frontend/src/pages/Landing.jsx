import { Fragment } from "react";
import "./Landing.css";

const STEPS = [
  {
    number: "01",
    title: "Scan or Search",
    text: "Scan a barcode, photograph a label, or search a product by name.",
  },
  {
    number: "02",
    title: "Check the Details",
    text: "See the ingredients and the nutrition values in one place.",
  },
  {
    number: "03",
    title: "Get a Health Score",
    text: "A score from 0 to 100 with clear reasons behind it.",
  },
  {
    number: "04",
    title: "Choose Better",
    text: "Compare two products and pick the healthier one.",
  },
];

const FEATURES = [
  {
    number: "01",
    title: "Barcode & Label Scan",
    text: "Look up a product from its barcode, or read the ingredients and nutrition table from a photo of the label.",
  },
  {
    number: "02",
    title: "Health Score",
    text: "A machine learning model turns calories, sugar, fat, sodium and ingredients into one easy score.",
  },
  {
    number: "03",
    title: "Ingredient Analysis",
    text: "Spot added sugar, palm oil, additives and allergens, explained in simple words.",
  },
  {
    number: "04",
    title: "Compare Products",
    text: "Put two products side by side and see which one is healthier, and why.",
  },
];

const SAMPLE_NUTRITION = [
  ["Calories", "160", "kcal"],
  ["Sugar", "1.5", "g"],
  ["Fat", "8.5", "g"],
  ["Sodium", "250", "mg"],
];

const SAMPLE_BARS = [
  ["Sugar", "1.5 g", "sugar"],
  ["Total Fat", "8.5 g", "fat"],
  ["Sodium", "250 mg", "sodium"],
];

const SAMPLE_INGREDIENTS = ["Corn meal", "Vegetable oil", "Salt", "Spices"];

function Landing({ onLogin, onSignup }) {
  return (
    <div className="app landing">

      {/* NAVBAR */}

      <nav className="navbar">

        <div className="navbar-inner">

          <button
            className="logo"
            onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
          >
            <div className="logo-icon">N</div>
            <span>NutriVision</span>
          </button>

          <div className="nav-links">
            <a href="#home">Home</a>
            <a href="#how-it-works">How It Works</a>
            <a href="#features">Features</a>
            <a href="#about">About</a>
          </div>

          <div className="nav-actions">
            <button className="nav-login" onClick={onLogin}>
              Log in
            </button>

            <button className="nav-button" onClick={onSignup}>
              Get started
            </button>
          </div>

        </div>

      </nav>


      {/* HERO */}

      <section className="hero" id="home">

        <div className="hero-inner">

          <div className="hero-content">

            <div className="badge">Smart Food Analysis</div>

            <h1>
              Know What
              <br />
              <span>You Eat.</span>
            </h1>

            <p>
              Scan a barcode or a food label and see its health score,
              ingredients and healthier choices, all in one simple place.
            </p>

            <div className="hero-buttons">

              <button className="primary-button" onClick={onSignup}>
                Get Started Free
                <span>→</span>
              </button>

              <a href="#how-it-works" className="secondary-button">
                See How It Works
              </a>

            </div>

            <div className="hero-note">
              Simple • Smart • Consumer Friendly
            </div>

          </div>


          {/* SAMPLE PRODUCT CARD */}

          <div className="hero-visual">

            <div className="hero-glow"></div>

            <div className="hero-product-card">

              <div className="card-top">
                <span>PRODUCT ANALYSIS</span>
                <span className="status">SAMPLE</span>
              </div>

              <div className="product-info">

                <div className="product-icon">N</div>

                <div className="product-name">
                  <h3>Kurkure Masala Munch</h3>

                  <p>
                    Kurkure
                    <span>•</span>
                    Snacks
                  </p>
                </div>

              </div>

              <div className="hero-nutrition-grid">
                {SAMPLE_NUTRITION.map(([label, value, unit]) => (
                  <div className="hero-nutrition-item" key={label}>
                    <span>{label}</span>
                    <strong>{value}</strong>
                    <small>{unit}</small>
                  </div>
                ))}
              </div>

              <div className="analysis-box">
                <div className="analysis-icon">✓</div>

                <div>
                  <strong>Analysis Ready</strong>
                  <p>Nutrition and ingredients available</p>
                </div>
              </div>

            </div>

          </div>

        </div>

      </section>


      {/* HOW IT WORKS */}

      <section className="section" id="how-it-works">

        <div className="section-heading">

          <span>HOW IT WORKS</span>

          <h2>
            From a scan to
            <br />
            <span>food intelligence.</span>
          </h2>

          <p>
            NutriVision makes understanding packaged food simple.
            Scan, discover, and understand.
          </p>

        </div>

        <div className="steps">
          {STEPS.map((step, index) => (
            <Fragment key={step.number}>

              {index > 0 && <div className="step-line"></div>}

              <div className="step">
                <div className="step-number">{step.number}</div>
                <div className="step-icon">{step.number}</div>
                <h3>{step.title}</h3>
                <p>{step.text}</p>
              </div>

            </Fragment>
          ))}
        </div>

      </section>


      {/* FEATURES */}

      <section className="features-section" id="features">

        <div className="section-heading">

          <span>WHY NUTRIVISION</span>

          <h2>
            Everything you need to
            <br />
            <span>understand your food.</span>
          </h2>

        </div>

        <div className="feature-grid">
          {FEATURES.map((feature) => (
            <div className="feature-card" key={feature.number}>
              <div className="feature-icon">{feature.number}</div>
              <h3>{feature.title}</h3>
              <p>{feature.text}</p>
            </div>
          ))}
        </div>

      </section>


      {/* ANALYSIS PREVIEW */}

      <section className="preview-section">

        <div className="preview-text">

          <span>SMART ANALYSIS</span>

          <h2>
            Food information,
            <br />
            <span>made understandable.</span>
          </h2>

          <p>
            Instead of complicated nutrition tables, NutriVision shows
            product information in a clear and easy-to-understand format.
          </p>

          <button className="primary-button" onClick={onSignup}>
            Create Free Account
            <span>→</span>
          </button>

        </div>

        <div className="analysis-preview">

          <div className="preview-header">

            <div>
              <small>SAMPLE PRODUCT</small>
              <h3>Kurkure Masala Munch</h3>
            </div>

            <div className="score">
              <strong>72</strong>
              <span>Sample</span>
            </div>

          </div>

          {SAMPLE_BARS.map(([label, value, type]) => (
            <div className="progress-item" key={label}>

              <div>
                <span>{label}</span>
                <strong>{value}</strong>
              </div>

              <div className="progress">
                <div className={`progress-fill ${type}`}></div>
              </div>

            </div>
          ))}

          <div className="ingredient-preview">

            <div className="ingredient-title">
              <span>INGREDIENTS</span>
            </div>

            <div className="ingredients">
              {SAMPLE_INGREDIENTS.map((name) => (
                <span key={name}>{name}</span>
              ))}
            </div>

          </div>

        </div>

      </section>


      {/* CTA */}

      <section className="cta-section" id="about">

        <div className="cta-content">

          <div className="cta-icon">N</div>

          <h2>
            Your food has a story.
            <br />
            <span>Let's understand it.</span>
          </h2>

          <p>
            NutriVision turns food label data into meaningful information
            for everyday consumers.
          </p>

          <button className="primary-button" onClick={onSignup}>
            Start Exploring
            <span>→</span>
          </button>

        </div>

      </section>


      {/* FOOTER */}

      <footer>

        <div className="footer-logo">
          <div className="logo-icon">N</div>
          <strong>NutriVision</strong>
        </div>

        <p>Smart Food Label & Ingredient Analysis System</p>

        <span>© 2026 NutriVision. All rights reserved.</span>

      </footer>

    </div>
  );
}

export default Landing;