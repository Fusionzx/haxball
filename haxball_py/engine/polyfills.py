# engine/polyfills.py

class JSPolyfills:
    @staticmethod
    def generate(proxy: str | None = None, debug: bool = False) -> str:
        # Polyfills to simulate browser APIs in Node.js / QuickJS context
        return f"""
        globalThis.window = globalThis;
        globalThis.parent = globalThis;
        
        // Mock simple document
        globalThis.document = {{
            createElement: () => ({{
                setAttribute: () => {{}},
                appendChild: () => {{}},
                style: {{}}
            }}),
            getElementById: () => null,
            body: {{ appendChild: () => {{}} }}
        }};
        
        // Simple XMLHttpRequest stub if needed
        if (!globalThis.XMLHttpRequest) {{
            globalThis.XMLHttpRequest = class XMLHttpRequest {{
                open() {{}}
                send() {{}}
                setRequestHeader() {{}}
            }};
        }}
        """
