import { useEffect, useRef } from "react";
import { useAuth } from "../auth/AuthContext";
import { snapshotFromResult } from "../auth/history";

/**
 * Renders nothing. When it appears on screen it saves one entry in the
 * user's history. A failure is ignored on purpose: history is a bonus and
 * must never get in the way of the page.
 *
 *   <RecordScan key={productId} source="product" productId={productId} />
 *   <RecordScan source="barcode" result={result} barcode={barcode} />
 *   <RecordScan source="label" result={result} />
 */
function RecordScan({ source, productId, result, barcode }) {
  const { authFetch } = useAuth();
  const done = useRef(false);

  useEffect(() => {
    if (done.current) {
      return;
    }

    const body =
      source === "product"
        ? productId
          ? { source, product_id: productId }
          : null
        : snapshotFromResult(source, result, barcode);

    if (!body) {
      return;
    }

    done.current = true;

    authFetch("/history", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).catch(() => {});
  }, [source, productId, result, barcode, authFetch]);

  return null;
}

export default RecordScan;