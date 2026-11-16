/* Merchant payment settings. Do not invent wallet addresses or payment status.
   Configure only after merchant confirms exact USDT network and address.
   This static frontend cannot verify on-chain payment or gift delivery. */
window.SPEED_DRIFT_PAYMENT = Object.freeze({
  token: "USDT",
  network: "",
  walletAddress: "",
  displayAmount: ""
});
