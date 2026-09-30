import { useState } from "react";
import "./App.css";

import ScanProduct from "./pages/ScanProduct";
import ProductSearch from "./pages/ProductSearch";
import ProductDetails from "./pages/ProductDetails";

function App() {
  const [showScanner, setShowScanner] = useState(false);
  const [showProductSearch, setShowProductSearch] = useState(false);
  const [selectedProductId, setSelectedProductId] = useState(null);

  const openScanner = () => {
    setShowScanner(true);
    setShowProductSearch(false);
    setSelectedProductId(null);
  };

  const openProductSearch = () => {
    setShowProductSearch(true);
    setShowScanner(false);
    setSelectedProductId(null);
  };

  const goHome = () => {
    setShowScanner(false);
    setShowProductSearch(false);
    setSelectedProductId(null);
  };

  const openProductDetails = (productId) => {
    setSelectedProductId(productId);
    setShowProductSearch(false);
    setShowScanner(false);
  };

  if (showScanner) {
    return <ScanProduct onBack={goHome} />;
  }

  if (showProductSearch) {
    return (
      <ProductSearch
        onBack={goHome}
        onProductSelect={openProductDetails}
      />
    );
  }

  if (selectedProductId) {
    return (
      <ProductDetails
        productId={selectedProductId}
        onBack={() => {
          setSelectedProductId(null);
          setShowProductSearch(true);
        }}
      />
    );
  }

  return (
    <div className="app">

      {/* NAVBAR */}

      <nav className="navbar">

        <div className="navbar-inner">

          <button
            className="logo"
            onClick={goHome}
          >
            <div className="logo-icon">
              N
            </div>

            <span>
              NutriVision
            </span>
          </button>

          <div className="nav-links">

            <a href="#home">
              Home
            </a>

            <a href="#how-it-works">
              How It Works
            </a>

            <a href="#features">
              Features
            </a>

            <a href="#about">
              About
            </a>

          </div>

          <div className="nav-actions">

            <button
              className="nav-button"
              onClick={openScanner}
            >
              Scan Product
            </button>

            <button
              className="nav-button"
              onClick={openProductSearch}
            >
              Search Product
            </button>

          </div>

        </div>

      </nav>


      {/* HERO */}

      <section
        className="hero"
        id="home"
      >

        <div className="hero-inner">

          <div className="hero-content">

            <div className="badge">
              Smart Food Analysis
            </div>

            <h1>
              Know What
              <br />
              <span>You Eat.</span>
            </h1>

            <p>
              Search a food product and discover its
              nutritional information, ingredients, and
              intelligent food analysis in one simple place.
            </p>

            <div className="hero-buttons">

              <button
                className="primary-button"
                onClick={openProductSearch}
              >
                Search Your Product
                <span>→</span>
              </button>

              <a
                href="#how-it-works"
                className="secondary-button"
              >
                See How It Works
              </a>

            </div>

            <div className="hero-note">
              Simple • Smart • Consumer Friendly
            </div>

          </div>


          {/* HERO PRODUCT PREVIEW */}

          <div className="hero-visual">

            <div className="hero-glow"></div>

            <div className="hero-product-card">

              <div className="card-top">

                <span>
                  PRODUCT ANALYSIS
                </span>

                <span className="status">
                  LIVE
                </span>

              </div>


              <div className="product-info">

                <div className="product-icon">
                  N
                </div>

                <div className="product-name">

                  <h3>
                    Kurkure Masala Munch
                  </h3>

                  <p>
                    Kurkure
                    <span>•</span>
                    Snacks
                  </p>

                </div>

              </div>


              <div className="hero-nutrition-grid">

                <div className="hero-nutrition-item">

                  <span>
                    Calories
                  </span>

                  <strong>
                    160
                  </strong>

                  <small>
                    kcal
                  </small>

                </div>


                <div className="hero-nutrition-item">

                  <span>
                    Sugar
                  </span>

                  <strong>
                    1.5
                  </strong>

                  <small>
                    g
                  </small>

                </div>


                <div className="hero-nutrition-item">

                  <span>
                    Fat
                  </span>

                  <strong>
                    8.5
                  </strong>

                  <small>
                    g
                  </small>

                </div>


                <div className="hero-nutrition-item">

                  <span>
                    Sodium
                  </span>

                  <strong>
                    250
                  </strong>

                  <small>
                    mg
                  </small>

                </div>

              </div>


              <div className="analysis-box">

                <div className="analysis-icon">
                  ✓
                </div>

                <div>

                  <strong>
                    Analysis Ready
                  </strong>

                  <p>
                    Nutrition and ingredients available
                  </p>

                </div>

              </div>

            </div>

          </div>

        </div>

      </section>


      {/* HOW IT WORKS */}

      <section
        className="section"
        id="how-it-works"
      >

        <div className="section-heading">

          <span>
            HOW IT WORKS
          </span>

          <h2>
            From product search to
            <br />
            <span>food intelligence.</span>
          </h2>

          <p>
            NutriVision makes understanding packaged
            food simple. Search, discover, and understand.
          </p>

        </div>


        <div className="steps">

          <div className="step">

            <div className="step-number">
              01
            </div>

            <div className="step-icon">
              01
            </div>

            <h3>
              Find Product
            </h3>

            <p>
              Search for your packaged food product
              using its name.
            </p>

          </div>


          <div className="step-line"></div>


          <div className="step">

            <div className="step-number">
              02
            </div>

            <div className="step-icon">
              02
            </div>

            <h3>
              View Details
            </h3>

            <p>
              View product information, ingredients,
              and nutritional values.
            </p>

          </div>


          <div className="step-line"></div>


          <div className="step">

            <div className="step-number">
              03
            </div>

            <div className="step-icon">
              03
            </div>

            <h3>
              Analyze
            </h3>

            <p>
              Nutrition and ingredient information
              is analyzed.
            </p>

          </div>


          <div className="step-line"></div>


          <div className="step">

            <div className="step-number">
              04
            </div>

            <div className="step-icon">
              04
            </div>

            <h3>
              Understand
            </h3>

            <p>
              Get simple and understandable food
              insights.
            </p>

          </div>

        </div>

      </section>


      {/* FEATURES */}

      <section
        className="features-section"
        id="features"
      >

        <div className="section-heading">

          <span>
            WHY NUTRIVISION
          </span>

          <h2>
            Everything you need to
            <br />
            <span>understand your food.</span>
          </h2>

        </div>


        <div className="feature-grid">

          <div className="feature-card">

            <div className="feature-icon">
              01
            </div>

            <h3>
              Product Identification
            </h3>

            <p>
              Search and identify packaged food
              products from the NutriVision dataset.
            </p>

          </div>


          <div className="feature-card">

            <div className="feature-icon">
              02
            </div>

            <h3>
              Nutrition Analysis
            </h3>

            <p>
              Understand calories, sugar, fats, protein,
              sodium and other nutritional values.
            </p>

          </div>


          <div className="feature-card">

            <div className="feature-icon">
              03
            </div>

            <h3>
              Ingredient Analysis
            </h3>

            <p>
              Explore the ingredients present in your
              food product with simple explanations.
            </p>

          </div>


          <div className="feature-card">

            <div className="feature-icon">
              04
            </div>

            <h3>
              Intelligent Insights
            </h3>

            <p>
              Data-driven analysis helps turn food
              information into meaningful insights.
            </p>

          </div>

        </div>

      </section>


      {/* ANALYSIS PREVIEW */}

      <section className="preview-section">

        <div className="preview-text">

          <span>
            SMART ANALYSIS
          </span>

          <h2>
            Food information,
            <br />
            <span>made understandable.</span>
          </h2>

          <p>
            Instead of showing complicated nutritional
            tables, NutriVision presents product information
            in a clear and easy-to-understand format.
          </p>

          <button
            className="primary-button"
            onClick={openProductSearch}
          >
            Explore Products
            <span>→</span>
          </button>

        </div>


        <div className="analysis-preview">

          <div className="preview-header">

            <div>

              <small>
                PRODUCT
              </small>

              <h3>
                Kurkure Masala Munch
              </h3>

            </div>

            <div className="score">

              <strong>
                72
              </strong>

              <span>
                Analysis
              </span>

            </div>

          </div>


          <div className="progress-item">

            <div>

              <span>
                Sugar
              </span>

              <strong>
                1.5 g
              </strong>

            </div>

            <div className="progress">

              <div className="progress-fill sugar"></div>

            </div>

          </div>


          <div className="progress-item">

            <div>

              <span>
                Total Fat
              </span>

              <strong>
                8.5 g
              </strong>

            </div>

            <div className="progress">

              <div className="progress-fill fat"></div>

            </div>

          </div>


          <div className="progress-item">

            <div>

              <span>
                Sodium
              </span>

              <strong>
                250 mg
              </strong>

            </div>

            <div className="progress">

              <div className="progress-fill sodium"></div>

            </div>

          </div>


          <div className="ingredient-preview">

            <div className="ingredient-title">

              <span>
                INGREDIENTS
              </span>

              <span>
                View all →
              </span>

            </div>

            <div className="ingredients">

              <span>
                Corn meal
              </span>

              <span>
                Vegetable oil
              </span>

              <span>
                Salt
              </span>

              <span>
                Spices
              </span>

            </div>

          </div>

        </div>

      </section>


      {/* CTA */}

      <section
        className="cta-section"
        id="about"
      >

        <div className="cta-content">

          <div className="cta-icon">
            N
          </div>

          <h2>
            Your food has a story.
            <br />
            <span>Let's understand it.</span>
          </h2>

          <p>
            NutriVision transforms food product data
            into meaningful information for everyday
            consumers.
          </p>

          <button
            className="primary-button"
            onClick={openProductSearch}
          >
            Start Exploring
            <span>→</span>
          </button>

        </div>

      </section>


      {/* FOOTER */}

      <footer>

        <div className="footer-logo">

          <div className="logo-icon">
            N
          </div>

          <strong>
            NutriVision
          </strong>

        </div>

        <p>
          Smart Food Label & Ingredient Analysis System
        </p>

        <span>
          © 2026 NutriVision. All rights reserved.
        </span>

      </footer>

    </div>
  );
}

export default App;