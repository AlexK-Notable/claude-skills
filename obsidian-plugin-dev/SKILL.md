---
name: obsidian-plugin-dev
description: Developing Obsidian plugins with TypeScript, React, and the Obsidian API
---

# Obsidian Plugin Development

**Purpose:** Build Obsidian plugins using TypeScript, React integration, and the Obsidian API.

**Use this skill when:**
- Creating new Obsidian plugins
- Adding features to existing plugins
- Working with Obsidian API (Plugin, View, Modal, Settings)
- Integrating React components into Obsidian
- Debugging plugin issues

---

## Plugin Structure

```
obsidian-plugin/
├── src/
│   ├── main.ts           # Plugin entry point (extends Plugin)
│   ├── views/            # Custom views
│   ├── modals/           # Modal dialogs
│   ├── settings.ts       # Settings tab
│   └── components/       # React components (if using React)
├── manifest.json         # Plugin metadata
├── package.json          # Dependencies
├── tsconfig.json         # TypeScript config
├── esbuild.config.mjs    # Build configuration
└── styles.css            # Plugin styles

## Main Plugin Class

```typescript
import { Plugin, TFile, Notice } from 'obsidian';
import { MyPluginSettings, DEFAULT_SETTINGS } from './settings';
import { MySettingTab } from './settingTab';

export default class MyPlugin extends Plugin {
    settings: MyPluginSettings;

    async onload() {
        console.log('Loading MyPlugin');

        // Load settings
        await this.loadSettings();

        // Add ribbon icon
        this.addRibbonIcon('dice', 'My Plugin', () => {
            new Notice('Hello from MyPlugin!');
        });

        // Add command
        this.addCommand({
            id: 'my-command',
            name: 'My Command',
            callback: () => {
                this.runCommand();
            }
        });

        // Add settings tab
        this.addSettingTab(new MySettingTab(this.app, this));

        // Register view (if using custom views)
        this.registerView(
            'my-view',
            (leaf) => new MyView(leaf, this)
        );
    }

    onunload() {
        console.log('Unloading MyPlugin');
    }

    async loadSettings() {
        this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
    }

    async saveSettings() {
        await this.saveData(this.settings);
    }

    async runCommand() {
        // Command logic
        new Notice('Command executed!');
    }
}
```

---

## Settings Management

```typescript
// settings.ts
export interface MyPluginSettings {
    apiKey: string;
    enableFeature: boolean;
    customValue: number;
}

export const DEFAULT_SETTINGS: MyPluginSettings = {
    apiKey: '',
    enableFeature: true,
    customValue: 10
};

// settingTab.ts
import { App, PluginSettingTab, Setting } from 'obsidian';
import MyPlugin from './main';

export class MySettingTab extends PluginSettingTab {
    plugin: MyPlugin;

    constructor(app: App, plugin: MyPlugin) {
        super(app, plugin);
        this.plugin = plugin;
    }

    display(): void {
        const { containerEl } = this;
        containerEl.empty();

        containerEl.createEl('h2', { text: 'My Plugin Settings' });

        new Setting(containerEl)
            .setName('API Key')
            .setDesc('Enter your API key')
            .addText(text => text
                .setPlaceholder('Enter API key')
                .setValue(this.plugin.settings.apiKey)
                .onChange(async (value) => {
                    this.plugin.settings.apiKey = value;
                    await this.plugin.saveSettings();
                }));

        new Setting(containerEl)
            .setName('Enable Feature')
            .setDesc('Enable the special feature')
            .addToggle(toggle => toggle
                .setValue(this.plugin.settings.enableFeature)
                .onChange(async (value) => {
                    this.plugin.settings.enableFeature = value;
                    await this.plugin.saveSettings();
                }));
    }
}
```

---

## React Integration

```typescript
// main.ts - Register React view
import { ItemView, WorkspaceLeaf } from 'obsidian';
import * as React from 'react';
import * as ReactDOM from 'react-dom';
import { MyReactComponent } from './components/MyReactComponent';

export class MyReactView extends ItemView {
    constructor(leaf: WorkspaceLeaf) {
        super(leaf);
    }

    getViewType(): string {
        return 'my-react-view';
    }

    getDisplayText(): string {
        return 'My React View';
    }

    async onOpen() {
        const container = this.containerEl.children[1];
        container.empty();

        // Render React component
        ReactDOM.render(
            <MyReactComponent app={this.app} />,
            container
        );
    }

    async onClose() {
        // Cleanup React
        ReactDOM.unmountComponentAtNode(this.containerEl.children[1]);
    }
}

// components/MyReactComponent.tsx
import * as React from 'react';
import { App } from 'obsidian';

interface Props {
    app: App;
}

export const MyReactComponent: React.FC<Props> = ({ app }) => {
    const [count, setCount] = React.useState(0);

    const handleClick = () => {
        // Access Obsidian API
        const files = app.vault.getMarkdownFiles();
        console.log(`Vault has ${files.length} files`);
        setCount(count + 1);
    };

    return (
        <div>
            <h1>My React Component</h1>
            <button onClick={handleClick}>
                Clicked {count} times
            </button>
        </div>
    );
};
```

---

## Working with Files

```typescript
import { TFile, TFolder, Notice } from 'obsidian';

// Get all markdown files
const files = this.app.vault.getMarkdownFiles();

// Read file content
const file = this.app.vault.getAbstractFileByPath('path/to/file.md');
if (file instanceof TFile) {
    const content = await this.app.vault.read(file);
    console.log(content);
}

// Modify file
await this.app.vault.modify(file, newContent);

// Create file
await this.app.vault.create('path/to/new-file.md', 'Content here');

// Delete file
await this.app.vault.delete(file);

// Get frontmatter
const cache = this.app.metadataCache.getFileCache(file);
const frontmatter = cache?.frontmatter;
```

---

## Modals

```typescript
import { Modal, App, Setting } from 'obsidian';

export class MyModal extends Modal {
    result: string;
    onSubmit: (result: string) => void;

    constructor(app: App, onSubmit: (result: string) => void) {
        super(app);
        this.onSubmit = onSubmit;
    }

    onOpen() {
        const { contentEl } = this;

        contentEl.createEl('h2', { text: 'Enter Value' });

        new Setting(contentEl)
            .setName('Value')
            .addText(text => text.onChange(value => {
                this.result = value;
            }));

        new Setting(contentEl)
            .addButton(btn => btn
                .setButtonText('Submit')
                .setCta()
                .onClick(() => {
                    this.close();
                    this.onSubmit(this.result);
                }));
    }

    onClose() {
        const { contentEl } = this;
        contentEl.empty();
    }
}

// Usage
new MyModal(this.app, (result) => {
    new Notice(`You entered: ${result}`);
}).open();
```

---

## Build Configuration (esbuild)

```javascript
// esbuild.config.mjs
import esbuild from 'esbuild';
import process from 'process';
import builtins from 'builtin-modules';

const prod = process.argv[2] === 'production';

esbuild.build({
    entryPoints: ['src/main.ts'],
    bundle: true,
    external: [
        'obsidian',
        'electron',
        '@codemirror/autocomplete',
        '@codemirror/collab',
        '@codemirror/commands',
        '@codemirror/language',
        '@codemirror/lint',
        '@codemirror/search',
        '@codemirror/state',
        '@codemirror/view',
        '@lezer/common',
        '@lezer/highlight',
        '@lezer/lr',
        ...builtins
    ],
    format: 'cjs',
    target: 'es2018',
    logLevel: 'info',
    sourcemap: prod ? false : 'inline',
    treeShaking: true,
    outfile: 'main.js',
}).catch(() => process.exit(1));
```

---

## manifest.json

```json
{
    "id": "my-plugin",
    "name": "My Plugin",
    "version": "1.0.0",
    "minAppVersion": "0.15.0",
    "description": "Plugin description",
    "author": "Your Name",
    "authorUrl": "https://github.com/username",
    "isDesktopOnly": false
}
```

---

## package.json

```json
{
    "name": "obsidian-my-plugin",
    "version": "1.0.0",
    "description": "My Obsidian Plugin",
    "main": "main.js",
    "scripts": {
        "dev": "node esbuild.config.mjs",
        "build": "node esbuild.config.mjs production"
    },
    "keywords": ["obsidian", "obsidian-plugin"],
    "author": "Your Name",
    "license": "MIT",
    "devDependencies": {
        "@types/node": "^16.11.6",
        "@types/react": "^18.0.0",
        "@types/react-dom": "^18.0.0",
        "@typescript-eslint/eslint-plugin": "^5.29.0",
        "@typescript-eslint/parser": "^5.29.0",
        "builtin-modules": "^3.3.0",
        "esbuild": "0.17.3",
        "obsidian": "latest",
        "tslib": "2.4.0",
        "typescript": "4.7.4"
    },
    "dependencies": {
        "react": "^18.2.0",
        "react-dom": "^18.2.0"
    }
}
```

---

## Development Workflow

### 1. Initial Setup
```bash
# Clone Obsidian sample plugin or create structure
npm install

# Link to Obsidian vault for testing
ln -s $(pwd) ~/path/to/vault/.obsidian/plugins/my-plugin
```

### 2. Development
```bash
# Build and watch for changes
npm run dev

# In Obsidian: Enable plugin in Settings > Community Plugins
# Reload plugin: Ctrl/Cmd + P → "Reload app without saving"
```

### 3. Testing
- Make changes to TypeScript files
- esbuild rebuilds automatically
- Reload Obsidian to see changes
- Check console for errors (Ctrl/Cmd + Shift + I)

### 4. Release
```bash
# Build production version
npm run build

# Update manifest.json version
# Create GitHub release with main.js, manifest.json, styles.css
```

---

## Common Patterns

### Access Active File
```typescript
const activeFile = this.app.workspace.getActiveFile();
if (activeFile) {
    const content = await this.app.vault.read(activeFile);
}
```

### Listen to File Changes
```typescript
this.registerEvent(
    this.app.vault.on('modify', (file) => {
        if (file instanceof TFile) {
            console.log('File modified:', file.path);
        }
    })
);
```

### Add Status Bar Item
```typescript
const statusBarItem = this.addStatusBarItem();
statusBarItem.setText('Status: Ready');
```

### Register Markdown Post Processor
```typescript
this.registerMarkdownPostProcessor((element, context) => {
    const codeBlocks = element.findAll('code');
    codeBlocks.forEach(code => {
        // Process code blocks
    });
});
```

---

## Debugging

### Console Logging
```typescript
console.log('Debug info');
console.error('Error info');

// Access console: Ctrl/Cmd + Shift + I
```

### Notices for User Feedback
```typescript
import { Notice } from 'obsidian';

new Notice('Success!', 5000);  // Shows for 5 seconds
new Notice('Error occurred', 0);  // Shows indefinitely
```

### Check Plugin Load
```typescript
async onload() {
    console.log('MyPlugin loaded');  // Should appear in console
}
```

---

## Key APIs

**App:** `this.app` - Main Obsidian app instance
**Vault:** `this.app.vault` - File system operations
**Workspace:** `this.app.workspace` - UI and editor operations
**MetadataCache:** `this.app.metadataCache` - File metadata and links
**FileManager:** `this.app.fileManager` - File operations helper

---

**When this skill activates:**
- Working in `obsidian-*/**/*.ts` or `obsidian-*/**/*.tsx` files
- Keywords: "obsidian plugin", "obsidian api", "plugin development"
- Patterns: `extends Plugin`, `from "obsidian"`, manifest.json editing

**Use explicitly for:**
- Creating new Obsidian plugins
- Adding features to existing plugins
- Debugging plugin issues
- React integration with Obsidian
