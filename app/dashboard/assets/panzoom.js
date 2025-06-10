(function () {
  function init() {
    const wrapper = document.getElementById("board-wrapper");
    const container = document.getElementById("board-container");
    if (!wrapper || !container) return false;

    let isDragging = false, startX = 0, startY = 0;

    wrapper.addEventListener("mousedown", (e) => {
      if (e.button !== 0) return;
      if (e.target.closest(".react-grid-item")) return;

      isDragging = true;
      wrapper.style.cursor = "grabbing";
      startX = e.clientX + wrapper.scrollLeft;
      startY = e.clientY + wrapper.scrollTop;
      e.preventDefault();
    });

    wrapper.addEventListener("mousemove", (e) => {
      if (!isDragging) return;
      wrapper.scrollLeft = startX - e.clientX;
      wrapper.scrollTop = startY - e.clientY;
    });

    ["mouseup", "mouseleave"].forEach(evt =>
      wrapper.addEventListener(evt, () => {
        isDragging = false;
        wrapper.style.cursor = "grab";
      })
    );

    let scale = 1.0;
    const MIN = 0.4, MAX = 2.0, STEP = 0.05;

    wrapper.addEventListener("wheel", (e) => {
      if (e.ctrlKey) return;
      e.preventDefault();

      const rect = wrapper.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;
      
      const scrollX = wrapper.scrollLeft;
      const scrollY = wrapper.scrollTop;
      const contentX = mouseX + scrollX;
      const contentY = mouseY + scrollY;
      
      const oldScale = scale;
      
      const delta = e.deltaY < 0 ? STEP : -STEP;
      scale = Math.min(MAX, Math.max(MIN, scale + delta));
      
      if (scale === oldScale) return;
      
      container.style.transform = `scale(${scale})`;
      container.style.transformOrigin = '0 0';
      
      const scaleDiff = scale / oldScale;
      const newScrollX = contentX * scaleDiff - mouseX;
      const newScrollY = contentY * scaleDiff - mouseY;
      
      wrapper.scrollTo({
        left: newScrollX,
        top: newScrollY,
        behavior: 'auto'
      });
    }, { passive: false });

    const zoomIndicator = document.createElement('div');
    zoomIndicator.id = 'zoom-indicator';
    zoomIndicator.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      background: rgba(0,0,0,0.7);
      color: white;
      padding: 8px 12px;
      border-radius: 4px;
      font-size: 14px;
      z-index: 1000;
      display: none;
    `;
    document.body.appendChild(zoomIndicator);

    let zoomTimeout;
    wrapper.addEventListener("wheel", () => {
      zoomIndicator.textContent = `${Math.round(scale * 100)}%`;
      zoomIndicator.style.display = 'block';
      clearTimeout(zoomTimeout);
      zoomTimeout = setTimeout(() => {
        zoomIndicator.style.display = 'none';
      }, 1500);
    });

    return true;
  }

  if (!init()) {
    const mo = new MutationObserver(() => {
      if (init()) mo.disconnect();
    });
    mo.observe(document.body, { childList: true, subtree: true });
  }
})();