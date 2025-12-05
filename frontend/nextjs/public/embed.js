(function () {
    window.AIResearchAssistant = {
        init: function () {
            const parentApiUrl = localStorage.getItem("AI_RESEARCH_API_URL");

            // Create container
            const container = document.createElement("div");
            container.id = "ai-research-container";
            container.style.width = "100%";
            container.style.height = "100vh";
            container.style.overflow = "hidden"; // Hide scrollbar

            // Create iframe
            const iframe = document.createElement("iframe");
            iframe.src = "https://research-assistant.dev" + (parentApiUrl ? "?AI_RESEARCH_API_URL=" + parentApiUrl : "");
            iframe.style.width = "100%";
            iframe.style.border = "none";
            iframe.style.height = "100%";
            iframe.style.overflow = "hidden";

            // Add custom styles to hide scrollbars
            const style = document.createElement("style");
            style.textContent = `
                #ai-research-container {
                    -ms-overflow-style: none;  /* IE and Edge */
                    scrollbar-width: none;     /* Firefox */
                }
                #ai-research-container::-webkit-scrollbar {
                    display: none;             /* Chrome, Safari and Opera */
                }
                #ai-research-container iframe {
                    -ms-overflow-style: none;
                    scrollbar-width: none;
                }
                #ai-research-container iframe::-webkit-scrollbar {
                    display: none;
                }
            `;
            document.head.appendChild(style);

            // Add iframe to container
            container.appendChild(iframe);
            document.currentScript.parentNode.insertBefore(container, document.currentScript);

            // Handle resize
            window.addEventListener("resize", () => {
                iframe.style.height = "100%";
            });

            // Ensure height is set after iframe loads
            iframe.addEventListener("load", () => {
                iframe.style.height = "100%";
            });
        },

        configure: function (options = {}) {
            if (options.height) {
                const iframe = document.querySelector("#ai-research-container iframe");
                if (iframe) {
                    iframe.style.height = options.height + "px";
                }
            }
        },
    };

    // Initialize when script loads
    window.AIResearchAssistant.init();
})();