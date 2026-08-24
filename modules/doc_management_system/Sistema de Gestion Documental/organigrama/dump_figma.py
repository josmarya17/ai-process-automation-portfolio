import os
import subprocess
import time
import http.server
import socketserver
import threading
import sys

def find_chrome():
    paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Users\Sist-JPinto\AppData\Local\Google\Chrome\Application\chrome.exe",
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    # Fallback to path
    return "chrome.exe"

def main():
    base_dir = r"c:\Users\Sist-JPinto\Desktop\Sistema de Gestion Documental\organigrama"
    temp_html_path = os.path.join(base_dir, "organigrama_Empresa Demo.html")
    output_html_path = os.path.join(base_dir, "organigrama_figma_Empresa Demo.html")
    
    if not os.path.exists(temp_html_path):
        print(f"Error: {temp_html_path} does not exist.")
        sys.exit(1)
        
    with open(temp_html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
        
    # Figma overrides: Hide header and toggles, make workspace white. Keep the original tree container padding intact!
    figma_overrides = """
        /* Figma optimization overrides */
        .header {
            display: none !important;
        }
        body {
            height: auto !important;
            overflow: visible !important;
            background-color: #FFFFFF !important;
        }
        .workspace {
            width: fit-content !important;
            min-width: 100% !important;
            height: auto !important;
            min-height: 100% !important;
            overflow: visible !important;
            background-color: #FFFFFF !important;
            background-image: none !important;
        }
        .tree-container {
            transform: none !important;
            background-color: #FFFFFF !important;
        }
        :root {
            --zoom-scale: 1.0 !important;
        }
        .toggle-btn {
            display: none !important;
        }
    """
    
    # Inject CSS overrides right before </head>
    html_with_figma_css = html_content.replace("</head>", f"<style>{figma_overrides}</style>\n</head>")
    
    # Define style computation JS script (does not alter the DOM structure, keeping original flex layout)
    figma_js_sync = """
        // Style properties to inline
        const styleProps = [
            'display', 'flex-direction', 'align-items', 'justify-content', 'gap',
            'background-color', 'color', 'font-family', 'font-size', 'font-weight', 'line-height',
            'text-transform', 'text-align', 'letter-spacing', 'box-sizing', 'overflow', 'box-shadow',
            'border-top-style', 'border-top-width', 'border-top-color',
            'border-right-style', 'border-right-width', 'border-right-color',
            'border-bottom-style', 'border-bottom-width', 'border-bottom-color',
            'border-left-style', 'border-left-width', 'border-left-color',
            'border-top-left-radius', 'border-top-right-radius', 'border-bottom-left-radius', 'border-bottom-right-radius',
            'padding-top', 'padding-right', 'padding-bottom', 'padding-left',
            'margin-top', 'margin-right', 'margin-bottom', 'margin-left'
        ];

        function inlineAllStyles(element) {
            const computed = window.getComputedStyle(element);
            styleProps.forEach(prop => {
                const val = computed.getPropertyValue(prop);
                if (val) {
                    element.style.setProperty(prop, val, 'important');
                }
            });
            
            // Recurse to all child nodes
            for (let i = 0; i < element.children.length; i++) {
                inlineAllStyles(element.children[i]);
            }
        }

        // Prepare DOM for Figma by drawing lines and inlining styles while preserving the original layout tree
        function prepareForFigma() {
            try {
                const treeContainer = document.getElementById('tree-container');
                
                // 1. Draw orthogonal connections to bake the SVG paths
                drawConnections();
                
                // 2. Inline visual styles on cards and combined node containers
                const cards = document.querySelectorAll('.card');
                const combinedContainers = document.querySelectorAll('.combined-node-container');
                
                cards.forEach(card => {
                    inlineAllStyles(card);
                });
                combinedContainers.forEach(cc => {
                    inlineAllStyles(cc);
                });
                
                // 3. Remove toggle buttons
                document.querySelectorAll('.toggle-btn').forEach(btn => btn.remove());
                
                // 4. Force tree container background to be solid white
                if (treeContainer) {
                    treeContainer.style.setProperty('background-color', '#FFFFFF', 'important');
                }
            } catch (err) {
                console.error("Preparation for Figma failed:", err);
            }
        }

        // Initialize for Figma (Synchronous)
        window.addEventListener('load', () => {
            isVertical = true;
            zoomScale = 1.0;
            document.documentElement.style.setProperty('--zoom-scale', 1.0);
            
            initTree();
            
            // Synchronous run to bake SVG and inline styles
            prepareForFigma();
        });
    """
    
    # Locate original onload handler
    original_onload = """        window.addEventListener('load', () => {
            applyZoom();
            initTree();
            setTimeout(drawConnections, 100);
        });"""
        
    html_final = html_with_figma_css.replace(original_onload, figma_js_sync)
        
    # Save temp HTML file
    temp_figma_temp_path = os.path.join(base_dir, "temp_figma_temp.html")
    with open(temp_figma_temp_path, "w", encoding="utf-8") as f:
        f.write(html_final)
        
    print("Flattening figma template written.")
    
    # Start local HTTP server
    PORT = 8999
    Handler = http.server.SimpleHTTPRequestHandler
    
    original_cwd = os.getcwd()
    os.chdir(base_dir)
    
    class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
        allow_reuse_address = True
        pass
        
    httpd = ThreadedTCPServer(("", PORT), Handler)
    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    print(f"HTTP Server started on port {PORT}")
    
    time.sleep(1)
    
    # Run Chrome
    chrome_path = find_chrome()
    url = f"http://localhost:{PORT}/temp_figma_temp.html"
    cmd = [
        chrome_path,
        "--headless",
        "--disable-gpu",
        "--dump-dom",
        url
    ]
    
    print("Running Chrome to dump DOM...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=15)
        rendered_html = result.stdout
        
        # Verify inlining exist in the dump
        if rendered_html and 'border-top-left-radius' in rendered_html:
            print("Successfully dumped rendered DOM using Enterprise SGC's exact layout preservation methodology!")
            with open(output_html_path, "w", encoding="utf-8") as f:
                f.write(rendered_html)
            print(f"Figma-ready Empresa Demo HTML saved to: {output_html_path}")
        else:
            print("Warning: Could not verify if styles were inlined. Saving anyway.")
            if rendered_html:
                with open(output_html_path, "w", encoding="utf-8") as f:
                    f.write(rendered_html)
                print(f"HTML saved to: {output_html_path}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        httpd.shutdown()
        httpd.server_close()
        os.chdir(original_cwd)
        if os.path.exists(temp_figma_temp_path):
            os.remove(temp_figma_temp_path)
            
    print("Done!")

if __name__ == "__main__":
    main()
