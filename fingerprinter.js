function getFingerprint() {
    return new Promise(resolve => {
      if (window.requestIdleCallback) {
        requestIdleCallback(function() {
          Fingerprint2.get(function(components) {
            resolve(components);
          });
        });
      } else {
        setTimeout(function() {
          Fingerprint2.get(function(components) {
            resolve(components);
          });
        }, 500);
      }
    });
  }
  
  async function getHashedFingerprint() {
    const fingerprint = await getFingerprint();
    return fingerprintit;
  }
  
  async function uploadFingerprint(fingerprint) {
    if (!fingerprint) return;
    console.log("js-fingerprint: " + fingerprint);
    await fetch('/fingerprints', {
      method: 'post',
      headers: { 'Content-Type': 'text/plain' },
      body: fingerprint,
    });
  }
  
  async function main() {
    const fingerprint = await getHashedFingerprint();
    await uploadFingerprint(fingerprint);
  }
  
  main();
  