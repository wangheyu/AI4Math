(function () {
  const handledKeys = new Set([
    "[",
    "]",
    "1",
    "2",
    "4",
    "5",
    "8",
    "c",
    "C",
    "a",
    "A",
    "d",
    "D",
    "w",
    "W",
    "s",
    "S",
    "q",
    "Q",
    "e",
    "E",
    "r",
    "R",
    "h",
    "H",
    "ArrowLeft",
    "ArrowRight",
    "ArrowUp",
    "ArrowDown",
    "PageUp",
    "PageDown",
  ]);

  function isEditingTarget(target) {
    if (!target) {
      return false;
    }
    const tagName = (target.tagName || "").toUpperCase();
    return (
      tagName === "INPUT" ||
      tagName === "TEXTAREA" ||
      tagName === "SELECT" ||
      target.isContentEditable
    );
  }

  document.addEventListener(
    "keydown",
    function (event) {
      if (!handledKeys.has(event.key) || isEditingTarget(event.target)) {
        return;
      }

      event.preventDefault();
      window.coloradoTerrainLastKey = {
        key: event.key,
        shiftKey: event.shiftKey,
        altKey: event.altKey,
        ctrlKey: event.ctrlKey,
        metaKey: event.metaKey,
        ts: Date.now() + Math.random(),
      };
    },
    { passive: false }
  );
})();
