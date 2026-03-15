{
  "app": {
    "name": "Second Brain / Executive Assistant (Mobile V1)",
    "product_personality": [
      "calmly premium",
      "operator-grade",
      "quietly powerful",
      "offline-first trustworthy",
      "gesture-first mobile"
    ],
    "design_style_fusion": {
      "layout_principle": "Notion-like block clarity + Obsidian-like reading focus (long-form), wrapped in a modern bento-card shell",
      "visual_style": "Soft-neutral editorial minimalism with subtle texture/noise + precise Swiss-style spacing",
      "interaction_style": "Bottom-sheet flows, thumb-zone primary actions, small haptics-style motion (no gimmicks)"
    },
    "success_actions": [
      "Create a note quickly",
      "Edit blocks without friction",
      "Import/export markdown confidently",
      "Generate a workflow graph and understand it at-a-glance",
      "Trust that data is local-first"
    ]
  },

  "typography": {
    "google_fonts_import": {
      "note": "Use in React Native via expo-google-fonts OR for Expo web via CSS import. Keep names consistent in tokens.",
      "families": [
        {
          "name": "Space Grotesk",
          "weights": ["400", "500", "600", "700"],
          "usage": "UI headings, screen titles, primary navigation"
        },
        {
          "name": "Figtree",
          "weights": ["400", "500", "600"],
          "usage": "Body, editor text, settings labels"
        },
        {
          "name": "Source Code Pro",
          "weights": ["400", "500"],
          "usage": "Monospace for code blocks, JSON previews, debug panels"
        }
      ]
    },
    "type_scale_tailwind": {
      "h1": "text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight",
      "h2": "text-base md:text-lg font-medium text-muted-foreground",
      "screen_title": "text-xl font-semibold tracking-tight",
      "section_title": "text-sm font-semibold uppercase tracking-wider text-muted-foreground",
      "body": "text-sm md:text-base leading-6",
      "small": "text-xs leading-5 text-muted-foreground"
    },
    "editor_readability": {
      "line_length": "Aim 60–75 characters for reading areas (web); in mobile, use generous padding and 1.55–1.7 line-height.",
      "default_editor": "Figtree 16–17px equivalent, slightly warm foreground",
      "monospace": "Source Code Pro for fenced blocks"
    }
  },

  "color_system": {
    "notes": [
      "Avoid purple (AI restriction).",
      "No heavy gradients; if used, keep under 20% viewport and only as decorative hero/background.",
      "Design for long sessions: warm neutrals + ocean-teal accents."
    ],
    "palette_hex": {
      "paper": "#FAF7F2",
      "canvas": "#F6F2EA",
      "surface": "#FFFFFF",
      "ink": "#111418",
      "ink_soft": "#2A3138",
      "muted": "#6B7280",
      "border": "#E7E1D8",
      "teal": "#2CB1A1",
      "teal_deep": "#0E776B",
      "sand": "#E7DCCB",
      "apricot": "#F4B08A",
      "success": "#1F9D7A",
      "warning": "#C58B2C",
      "danger": "#D1493F"
    },
    "shadcn_tokens_hsl": {
      "note": "Update /frontend/src/index.css tokens to match this aesthetic. These are HSL triplets used by shadcn.",
      "light": {
        "--background": "34 33% 96%",
        "--foreground": "210 18% 8%",
        "--card": "0 0% 100%",
        "--card-foreground": "210 18% 8%",
        "--popover": "0 0% 100%",
        "--popover-foreground": "210 18% 8%",
        "--primary": "174 58% 40%",
        "--primary-foreground": "0 0% 100%",
        "--secondary": "34 22% 91%",
        "--secondary-foreground": "210 18% 12%",
        "--muted": "34 20% 93%",
        "--muted-foreground": "215 10% 40%",
        "--accent": "174 35% 92%",
        "--accent-foreground": "174 70% 18%",
        "--destructive": "6 69% 54%",
        "--destructive-foreground": "0 0% 100%",
        "--border": "32 20% 86%",
        "--input": "32 20% 86%",
        "--ring": "174 58% 40%",
        "--radius": "14px"
      },
      "dark": {
        "note": "Optional later; keep true dark without gradients. Use teal only as accent.",
        "--background": "210 20% 6%",
        "--foreground": "0 0% 98%",
        "--card": "210 20% 8%",
        "--card-foreground": "0 0% 98%",
        "--popover": "210 20% 8%",
        "--popover-foreground": "0 0% 98%",
        "--primary": "174 58% 45%",
        "--primary-foreground": "210 20% 8%",
        "--secondary": "210 16% 14%",
        "--secondary-foreground": "0 0% 98%",
        "--muted": "210 16% 14%",
        "--muted-foreground": "215 10% 70%",
        "--accent": "174 25% 18%",
        "--accent-foreground": "0 0% 98%",
        "--destructive": "6 55% 42%",
        "--destructive-foreground": "0 0% 98%",
        "--border": "210 16% 16%",
        "--input": "210 16% 16%",
        "--ring": "174 58% 45%",
        "--radius": "14px"
      }
    },
    "allowed_gradients": {
      "rule": "Keep gradients decorative only; max ~20% viewport.",
      "examples": [
        "radial-gradient(1200px circle at 20% 0%, rgba(44,177,161,0.18), transparent 55%)",
        "radial-gradient(900px circle at 90% 10%, rgba(244,176,138,0.16), transparent 50%)"
      ]
    },
    "texture": {
      "css_noise_overlay": "Use a subtle noise layer via background-image (tiny svg/png) at opacity 0.04–0.07 on large backgrounds only.",
      "image_urls": [
        {
          "category": "texture",
          "description": "Teal-ish grain texture for subtle section overlays (use with low opacity).",
          "url": "https://images.unsplash.com/photo-1656788104365-579240e279a7?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzd8MHwxfHNlYXJjaHwyfHxtaW5pbWFsJTIwYWJzdHJhY3QlMjBncmFpbiUyMHRleHR1cmUlMjB0ZWFsfGVufDB8fHx0ZWFsfDE3NzM1Nzg1Nzh8MA&ixlib=rb-4.1.0&q=85"
        },
        {
          "category": "texture",
          "description": "Soft textile-like texture (good for blurred header strip backgrounds).",
          "url": "https://images.unsplash.com/photo-1585536598573-a3e38edde798?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzd8MHwxfHNlYXJjaHwzfHxtaW5pbWFsJTIwYWJzdHJhY3QlMjBncmFpbiUyMHRleHR1cmUlMjB0ZWFsfGVufDB8fHx0ZWFsfDE3NzM1Nzg1Nzh8MA&ixlib=rb-4.1.0&q=85"
        }
      ]
    }
  },

  "layout_and_grid": {
    "mobile_first_principles": [
      "Primary actions live in the bottom 1/3rd (thumb zone).",
      "Prefer bottom sheets/drawers for secondary actions (import/export, metadata, block tools).",
      "Keep reading surfaces calm: solid backgrounds, no gradients behind text."
    ],
    "spacing_system": {
      "base": "4pt",
      "recommendation": "Use 2–3x more spacing than default shadcn examples. Prefer padding 16–20 on mobile cards; 24+ on major screens.",
      "tokens": {
        "--space-1": "4px",
        "--space-2": "8px",
        "--space-3": "12px",
        "--space-4": "16px",
        "--space-5": "20px",
        "--space-6": "24px",
        "--space-8": "32px"
      }
    },
    "shell_structure": {
      "top": "Compact top bar with screen title + contextual actions (Search, New, More).",
      "middle": "Content area with ScrollArea; cards for lists; editor uses full-width reading column.",
      "bottom": "Persistent bottom nav (Notes, Workflow, Calendar, Settings) OR a floating create button + tab bar later."
    }
  },

  "components": {
    "component_path": {
      "primary": "/app/frontend/src/components/ui",
      "note": "Use these shadcn components as the baseline. You can extend styles, but keep API consistent."
    },
    "shadcn_recommended": [
      {
        "name": "Button",
        "path": "src/components/ui/button.jsx",
        "usage": "Primary CTAs, toolbar actions",
        "testing": "Add data-testid on every button"
      },
      {
        "name": "Input / Textarea",
        "path": "src/components/ui/input.jsx, src/components/ui/textarea.jsx",
        "usage": "Prompt input, note title, block text",
        "testing": "data-testid required"
      },
      {
        "name": "Card",
        "path": "src/components/ui/card.jsx",
        "usage": "Note list rows, workflow templates, settings sections"
      },
      {
        "name": "Tabs",
        "path": "src/components/ui/tabs.jsx",
        "usage": "Editor modes: Write / Preview / Outline"
      },
      {
        "name": "Sheet / Drawer",
        "path": "src/components/ui/sheet.jsx, src/components/ui/drawer.jsx",
        "usage": "Block tools, import/export, note metadata, quick actions"
      },
      {
        "name": "Command",
        "path": "src/components/ui/command.jsx",
        "usage": "Global search / command palette (very on-brand for power users)"
      },
      {
        "name": "ScrollArea",
        "path": "src/components/ui/scroll-area.jsx",
        "usage": "Long lists and editor surfaces"
      },
      {
        "name": "Separator",
        "path": "src/components/ui/separator.jsx",
        "usage": "List dividers in settings and metadata"
      },
      {
        "name": "Sonner",
        "path": "src/components/ui/sonner.jsx",
        "usage": "Toasts for import/export success/failure"
      },
      {
        "name": "Calendar",
        "path": "src/components/ui/calendar.jsx",
        "usage": "Google Calendar (later) / meeting preview (now placeholder allowed in UI later)"
      }
    ],
    "component_states": {
      "buttons": {
        "primary": {
          "shape": "rounded-xl",
          "shadow": "shadow-[0_10px_30px_rgba(17,20,24,0.10)]",
          "hover": "hover:brightness-[0.98]",
          "active": "active:scale-[0.98]",
          "focus": "focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        },
        "secondary": {
          "surface": "bg-secondary text-secondary-foreground border border-border",
          "hover": "hover:bg-accent"
        },
        "ghost": {
          "surface": "bg-transparent",
          "hover": "hover:bg-accent"
        }
      },
      "inputs": {
        "shape": "rounded-xl",
        "focus": "focus-visible:ring-2 focus-visible:ring-ring",
        "empty_state": "Use muted text + subtle helper copy"
      },
      "cards": {
        "shape": "rounded-2xl",
        "border": "border border-border",
        "hover": "hover:shadow-[0_14px_40px_rgba(17,20,24,0.10)]",
        "selected": "ring-2 ring-ring"
      }
    }
  },

  "screens_blueprints": {
    "notes_list": {
      "layout": "Top bar + search input + segmented filter tabs + card list",
      "key_components": ["Input", "Tabs", "Card", "ScrollArea", "Button"],
      "empty_state": "Illustration-free: use subtle icon + 2 lines of copy + Create Note CTA",
      "testids": [
        "notes-search-input",
        "notes-create-button",
        "notes-list-item",
        "notes-empty-state"
      ]
    },
    "note_editor": {
      "layout": "Title + block canvas (stacked blocks) + bottom sheet for block actions",
      "block_types": ["Paragraph", "Heading", "Bulleted list", "Checklist", "Quote", "Code"],
      "block_micro_interactions": [
        "Tap block to focus; show left handle + quick action mini-toolbar",
        "Long press opens reorder mode (subtle scale + haptic-like animation)",
        "Inline slash-command using Command component (later)"
      ],
      "testids": [
        "editor-title-input",
        "editor-block",
        "editor-add-block-button",
        "editor-more-actions-button"
      ]
    },
    "workflow_agent": {
      "layout": "Prompt input area + Generate button + webview canvas placeholder",
      "visual": "Teal accent for nodes/edges; keep canvas surface solid off-white",
      "testids": [
        "workflow-prompt-input",
        "workflow-generate-button",
        "workflow-canvas-webview"
      ]
    },
    "settings": {
      "layout": "Grouped cards (Account, Sync, Integrations, Storage)",
      "testids": [
        "settings-list",
        "settings-sign-in-button",
        "settings-export-button"
      ]
    }
  },

  "motion": {
    "principles": [
      "Motion is functional: reveal hierarchy, confirm actions, reduce uncertainty.",
      "Keep durations short; avoid bounce-heavy easing for a premium feel.",
      "Respect prefers-reduced-motion."
    ],
    "durations": {
      "fast": "120ms",
      "base": "180ms",
      "slow": "240ms"
    },
    "easing": {
      "standard": "cubic-bezier(0.2, 0.8, 0.2, 1)",
      "exit": "cubic-bezier(0.4, 0, 1, 1)"
    },
    "micro_interactions": [
      "Buttons: active scale 0.98; shadow tightens slightly",
      "Cards: hover (web) increases shadow; press (mobile) reduces opacity to 0.96",
      "Sheet/Drawer: slide up with slight fade; backdrop uses 0.25 opacity",
      "Toast: appear from bottom with minimal distance (12–16px)"
    ],
    "libraries": {
      "framer_motion_web_optional": {
        "install": "npm i framer-motion",
        "usage": "Only for Expo web previews / marketing-like screens; keep mobile-native animations via RN Animated/Reanimated later.",
        "note": "If used, never do transition: all."
      }
    }
  },

  "accessibility": {
    "rules": [
      "All tappable targets >= 44x44.",
      "Visible focus states on web (focus-visible ring).",
      "Color contrast: body text >= 4.5:1.",
      "Use semantic labels and aria-labels on icon-only buttons (web).",
      "Respect reduced motion settings."
    ]
  },

  "data_testid_convention": {
    "format": "kebab-case",
    "examples": [
      "notes-create-button",
      "editor-add-block-button",
      "workflow-generate-button",
      "import-md-confirm-button",
      "toast-import-success"
    ]
  },

  "implementation_tokens": {
    "css_custom_properties": {
      "note": "These can live in index.css (web) and mirrored in RN theme constants later.",
      ":root": {
        "--font-sans": "Figtree, ui-sans-serif, system-ui",
        "--font-display": "Space Grotesk, ui-sans-serif, system-ui",
        "--font-mono": "Source Code Pro, ui-monospace, SFMono-Regular",
        "--shadow-soft": "0 10px 30px rgba(17,20,24,0.10)",
        "--shadow-float": "0 18px 50px rgba(17,20,24,0.14)",
        "--radius-card": "16px",
        "--radius-control": "12px"
      }
    },
    "tailwind_patterns": {
      "screen_padding": "px-4 sm:px-6",
      "card": "rounded-2xl border border-border bg-card text-card-foreground",
      "glass_header_strip": "bg-white/70 backdrop-blur-md border-b border-border",
      "subtle_noise": "[mask-image:radial-gradient(white,transparent)] opacity-[0.06]"
    }
  },

  "instructions_to_main_agent": [
    "This repo currently contains a web React app at /app/frontend; the mobile Expo app will live at /app/mobile. Keep design tokens conceptually aligned but do not modify existing web UI unless asked.",
    "When creating any UI later (even placeholders), add data-testid to every interactive element and key informational text.",
    "Use shadcn components from /frontend/src/components/ui for web scaffolding and to keep styling consistent; for React Native, implement analogous components with matching tokens.",
    "Do NOT introduce purple. Prefer teal + warm neutrals.",
    "Do NOT use gradients except decorative background overlays under 20% viewport. Avoid gradients on reading surfaces.",
    "Avoid centered, symmetrical landing-page layout; use left-aligned editorial rhythm and bento grouping.",
    "If adding iconography: use lucide-react (web) / @expo/vector-icons (mobile) later. No emoji icons.",
    "Keep components in .js (not .tsx)."
  ]
}

---

<General UI UX Design Guidelines>  
    - You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms
    - You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text
   - NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json

 **GRADIENT RESTRICTION RULE**
NEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc
NEVER use dark gradients for logo, testimonial, footer etc
NEVER let gradients cover more than 20% of the viewport.
NEVER apply gradients to text-heavy content or reading areas.
NEVER use gradients on small UI elements (<100px width).
NEVER stack multiple gradient layers in the same viewport.

**ENFORCEMENT RULE:**
    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors

**How and where to use:**
   • Section backgrounds (not content backgrounds)
   • Hero section header content. Eg: dark to light to dark color
   • Decorative overlays and accent elements only
   • Hero section with 2-3 mild color
   • Gradients creation can be done for any angle say horizontal, vertical or diagonal

- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc**

</Font Guidelines>

- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead. 
   
- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.

- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.
   
- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly
    Eg: - if it implies playful/energetic, choose a colorful scheme
           - if it implies monochrome/minimal, choose a black–white/neutral scheme

**Component Reuse:**
	- Prioritize using pre-existing components from src/components/ui when applicable
	- Create new components that match the style and conventions of existing components when needed
	- Examine existing components to understand the project's component patterns before creating new ones

**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component

**Best Practices:**
	- Use Shadcn/UI as the primary component library for consistency and accessibility
	- Import path: ./components/[component-name]

**Export Conventions:**
	- Components MUST use named exports (export const ComponentName = ...)
	- Pages MUST use default exports (export default function PageName() {...})

**Toasts:**
  - Use `sonner` for toasts"
  - Sonner component are located in `/app/src/components/ui/sonner.tsx`

Use 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals.
</General UI UX Design Guidelines>
