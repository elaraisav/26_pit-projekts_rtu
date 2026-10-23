/* Chatgpt sakumlapas funkcionalitātes kods*/
document.querySelectorAll(".photo-carousel").forEach((carousel) => {
    const track = carousel.querySelector(".photo-track");
    const prevButton = carousel.querySelector(".prev");
    const nextButton = carousel.querySelector(".next");

    if (!track || !prevButton || !nextButton) {
        return;
    }

    function updateButtons() {
        const maxScroll = track.scrollWidth - track.clientWidth;

        prevButton.disabled = track.scrollLeft <= 1;
        nextButton.disabled = track.scrollLeft >= maxScroll - 1;
    }

    prevButton.addEventListener("click", () => {
        track.scrollBy({
            left: -track.clientWidth * 0.8,
            behavior: "smooth"
        });
    });

    nextButton.addEventListener("click", () => {
        track.scrollBy({
            left: track.clientWidth * 0.8,
            behavior: "smooth"
        });
    });

    track.addEventListener("scroll", updateButtons, {
        passive: true
    });

    window.addEventListener("resize", updateButtons);

    updateButtons();
});
