import { useState } from "react";
import { Html5Qrcode } from "html5-qrcode";
import "./ScanProduct.css";

function ScanProduct({ onBack }) {
  const [barcode, setBarcode] = useState("");
  const [scannerRunning, setScannerRunning] = useState(false);
  const [scanner, setScanner] = useState(null);

  const startScanner = async () => {
    try {
      const newScanner = new Html5Qrcode("barcode-reader");

      setScanner(newScanner);
      setScannerRunning(true);

      await newScanner.start(
        { facingMode: "environment" },
        {
          fps: 10,
          qrbox: {
            width: 300,
            height: 150,
          },
        },
        (decodedText) => {
          setBarcode(decodedText);

          newScanner
            .stop()
            .then(() => {
              setScannerRunning(false);
              setScanner(null);
            })
            .catch((error) => {
              console.error("Scanner stop error:", error);
              setScannerRunning(false);
              setScanner(null);
            });
        },
        () => {
          // Scanner is still searching for a barcode.
        }
      );
    } catch (error) {
      console.error("Camera error:", error);

      setScannerRunning(false);
      setScanner(null);

      alert(
        "Unable to access the camera. Please allow camera permission."
      );
    }
  };

  const stopScanner = async () => {
    if (!scanner) {
      return;
    }

    try {
      await scanner.stop();
      setScannerRunning(false);
      setScanner(null);
    } catch (error) {
      console.error("Scanner stop error:", error);
      setScannerRunning(false);
      setScanner(null);
    }
  };

  const handleFindProduct = () => {
    if (!barcode.trim()) {
      alert("Please scan or enter a barcode.");
      return;
    }

    console.log("Barcode:", barcode);

    // Backend connection will be added next.
  };

  return (
    <div className="scan-page">
      <div className="scan-container">

        <button
          className="back-button"
          onClick={onBack}
        >
          Back to Home
        </button>

        <h1>Scan Your Product</h1>

        <p className="scan-description">
          Scan the barcode of your food product to get
          nutrition and ingredient analysis.
        </p>

        <div className="scanner-box">

          <div id="barcode-reader"></div>

          {!scannerRunning && (
            <>
              <h2>Barcode Scanner</h2>

              <p>
                Place the product barcode inside the camera area.
              </p>

              <button
                className="camera-button"
                onClick={startScanner}
              >
                Open Camera
              </button>
            </>
          )}

          {scannerRunning && (
            <button
              className="camera-button"
              onClick={stopScanner}
            >
              Stop Camera
            </button>
          )}

        </div>

        <div className="divider">
          <span>OR</span>
        </div>

        <div className="manual-section">

          <h2>Enter Barcode Manually</h2>

          <input
            type="text"
            placeholder="Enter product barcode"
            value={barcode}
            onChange={(e) => setBarcode(e.target.value)}
          />

          <button
            className="find-button"
            onClick={handleFindProduct}
          >
            Find Product
          </button>

        </div>

      </div>
    </div>
  );
}

export default ScanProduct;