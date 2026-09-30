import { useState } from "react";
import "./ProductSearch.css";

function ProductSearch({ onBack, onProductSelect }) {
  const [searchText, setSearchText] = useState("");
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const searchProducts = async () => {
    if (!searchText.trim()) {
      setError("Please enter a product name.");
      setProducts([]);
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/products/search?q=${encodeURIComponent(
          searchText
        )}`
      );

      if (!response.ok) {
        throw new Error("Unable to search products.");
      }

      const data = await response.json();

      setProducts(data);

      if (data.length === 0) {
        setError("No products found.");
      }
    } catch (error) {
      console.error("Search error:", error);
      setError(
        "Unable to connect to the server. Please make sure the backend is running."
      );
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter") {
      searchProducts();
    }
  };

  return (
    <div className="product-search-page">

      <div className="product-search-container">

        <button
          className="back-button"
          onClick={onBack}
        >
          Back to Home
        </button>

        <h1>Find Your Product</h1>

        <p className="search-description">
          Search for a packaged food product to view its
          nutrition and ingredient information.
        </p>

        <div className="search-box">

          <input
            type="text"
            placeholder="Enter product name"
            value={searchText}
            onChange={(event) => setSearchText(event.target.value)}
            onKeyDown={handleKeyDown}
          />

          <button
            className="search-button"
            onClick={searchProducts}
          >
            Search
          </button>

        </div>

        {loading && (
          <p className="search-message">
            Searching products...
          </p>
        )}

        {error && !loading && (
          <p className="search-message">
            {error}
          </p>
        )}

        {!loading && products.length > 0 && (
          <div className="product-results">

            <h2>Search Results</h2>

            {products.map((product) => (

              <div
                className="product-card"
                key={product.id}
                onClick={() => onProductSelect(product.id)}
              >

                <div>
                  <h3>{product.product_name}</h3>

                  <p>
                    <strong>Brand:</strong>{" "}
                    {product.brand || "Not available"}
                  </p>

                  <p>
                    <strong>Category:</strong>{" "}
                    {product.category || "Not available"}
                  </p>

                  <p>
                    <strong>Serving Size:</strong>{" "}
                    {product.serving_size || "Not available"}
                  </p>
                </div>

                <button
                  className="view-product-button"
                  onClick={(event) => {
                    event.stopPropagation();
                    onProductSelect(product.id);
                  }}
                >
                  View Details
                </button>

              </div>

            ))}

          </div>
        )}

      </div>

    </div>
  );
}

export default ProductSearch;