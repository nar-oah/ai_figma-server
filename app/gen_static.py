from __future__ import annotations
import json
from app.domain import GenDoc


def get_uno(doc: GenDoc) -> str:
    root_css = "\n".join(f"  {key}: {val};" for key, val in sorted(doc.tokens.root.items()))
    class_css = "\n".join(f".{key} {{ {val} }}" for key, val in sorted(doc.tokens.classes.items()))
    return f"""import {{ defineConfig, presetUno }} from 'unocss'

const rootCss = `:root {{
{root_css}
}}`

const extraCss = `
{class_css}
`

export default defineConfig({{
  presets: [presetUno()],
  content: {{
    filesystem: ['src/**/*.{{svelte,ts,js}}'],
  }},
  preflights: [
    {{
      getCSS: () => `${{rootCss}}\\n${{extraCss}}`,
    }},
  ],
}})
"""


def get_css() -> str:
    return """@unocss preflights;
@unocss default;
@unocss utilities;

html,
body {
  margin: 0;
  min-height: 100%;
}

body {
  min-height: 100vh;
}

* {
  box-sizing: border-box;
}

p {
  margin: 0;
}
"""


def get_layout() -> str:
    return """<script lang="ts">
  import '../app.css'
</script>

<slot />
"""


def get_meta(doc: GenDoc) -> str:
    data = {
        "name": doc.name,
        "key": doc.key,
        "pages": [{"name": item.name, "route": item.route} for item in doc.pages],
        "components": [{"name": item.name, "tag": item.tag} for item in doc.comps],
        "warnings": doc.warns,
    }
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"
