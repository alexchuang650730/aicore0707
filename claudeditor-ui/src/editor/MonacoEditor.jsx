import React, { useRef, useEffect, useState, useCallback } from 'react';
import * as monaco from 'monaco-editor';
import { 
  Play, 
  Save, 
  FolderOpen, 
  Settings, 
  Search, 
  Replace,
  Maximize2,
  Minimize2,
  Code,
  FileText,
  Terminal
} from 'lucide-react';

// Monaco Editor 配置
const MONACO_CONFIG = {
  theme: 'vs-dark',
  fontSize: 14,
  fontFamily: 'JetBrains Mono, Consolas, Monaco, monospace',
  lineNumbers: 'on',
  minimap: { enabled: true },
  scrollBeyondLastLine: false,
  automaticLayout: true,
  wordWrap: 'on',
  tabSize: 2,
  insertSpaces: true,
  detectIndentation: true,
  folding: true,
  foldingStrategy: 'auto',
  showFoldingControls: 'always',
  unfoldOnClickAfterEndOfLine: false,
  bracketPairColorization: { enabled: true },
  guides: {
    bracketPairs: true,
    indentation: true
  },
  suggest: {
    showKeywords: true,
    showSnippets: true,
    showClasses: true,
    showFunctions: true,
    showVariables: true
  },
  quickSuggestions: {
    other: true,
    comments: true,
    strings: true
  }
};

// 支持的编程语言
const SUPPORTED_LANGUAGES = [
  { id: 'javascript', name: 'JavaScript', ext: '.js' },
  { id: 'typescript', name: 'TypeScript', ext: '.ts' },
  { id: 'python', name: 'Python', ext: '.py' },
  { id: 'java', name: 'Java', ext: '.java' },
  { id: 'cpp', name: 'C++', ext: '.cpp' },
  { id: 'csharp', name: 'C#', ext: '.cs' },
  { id: 'go', name: 'Go', ext: '.go' },
  { id: 'rust', name: 'Rust', ext: '.rs' },
  { id: 'php', name: 'PHP', ext: '.php' },
  { id: 'ruby', name: 'Ruby', ext: '.rb' },
  { id: 'html', name: 'HTML', ext: '.html' },
  { id: 'css', name: 'CSS', ext: '.css' },
  { id: 'scss', name: 'SCSS', ext: '.scss' },
  { id: 'json', name: 'JSON', ext: '.json' },
  { id: 'yaml', name: 'YAML', ext: '.yaml' },
  { id: 'markdown', name: 'Markdown', ext: '.md' },
  { id: 'sql', name: 'SQL', ext: '.sql' },
  { id: 'shell', name: 'Shell', ext: '.sh' },
  { id: 'dockerfile', name: 'Dockerfile', ext: 'Dockerfile' }
];

const MonacoEditor = ({ 
  onCodeChange, 
  onSave, 
  onRun,
  initialCode = '',
  language = 'javascript',
  readOnly = false,
  className = ''
}) => {
  const editorRef = useRef(null);
  const containerRef = useRef(null);
  const [editor, setEditor] = useState(null);
  const [currentLanguage, setCurrentLanguage] = useState(language);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [searchVisible, setSearchVisible] = useState(false);
  const [editorSettings, setEditorSettings] = useState(MONACO_CONFIG);
  const [code, setCode] = useState(initialCode);
  const [cursorPosition, setCursorPosition] = useState({ line: 1, column: 1 });
  const [selectionInfo, setSelectionInfo] = useState('');

  // 初始化Monaco编辑器
  useEffect(() => {
    if (containerRef.current && !editor) {
      // 配置Monaco环境
      monaco.editor.defineTheme('claude-dark', {
        base: 'vs-dark',
        inherit: true,
        rules: [
          { token: 'comment', foreground: '6A9955', fontStyle: 'italic' },
          { token: 'keyword', foreground: '569CD6', fontStyle: 'bold' },
          { token: 'string', foreground: 'CE9178' },
          { token: 'number', foreground: 'B5CEA8' },
          { token: 'function', foreground: 'DCDCAA' },
          { token: 'variable', foreground: '9CDCFE' },
          { token: 'type', foreground: '4EC9B0' }
        ],
        colors: {
          'editor.background': '#1e1e1e',
          'editor.foreground': '#d4d4d4',
          'editor.lineHighlightBackground': '#2d2d30',
          'editor.selectionBackground': '#264f78',
          'editor.inactiveSelectionBackground': '#3a3d41'
        }
      });

      const editorInstance = monaco.editor.create(containerRef.current, {
        value: initialCode,
        language: currentLanguage,
        theme: 'claude-dark',
        ...editorSettings,
        readOnly
      });

      setEditor(editorInstance);
      editorRef.current = editorInstance;

      // 监听代码变化
      editorInstance.onDidChangeModelContent(() => {
        const value = editorInstance.getValue();
        setCode(value);
        onCodeChange?.(value);
      });

      // 监听光标位置变化
      editorInstance.onDidChangeCursorPosition((e) => {
        setCursorPosition({
          line: e.position.lineNumber,
          column: e.position.column
        });
      });

      // 监听选择变化
      editorInstance.onDidChangeCursorSelection((e) => {
        const selection = editorInstance.getSelection();
        if (selection && !selection.isEmpty()) {
          const selectedText = editorInstance.getModel().getValueInRange(selection);
          setSelectionInfo(`${selectedText.length} chars selected`);
        } else {
          setSelectionInfo('');
        }
      });

      // 添加快捷键
      editorInstance.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
        handleSave();
      });

      editorInstance.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyR, () => {
        handleRun();
      });

      editorInstance.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyF, () => {
        setSearchVisible(true);
        editorInstance.getAction('actions.find').run();
      });

      editorInstance.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyH, () => {
        editorInstance.getAction('editor.action.startFindReplaceAction').run();
      });

      // 自动保存
      const autoSaveInterval = setInterval(() => {
        if (editorInstance.getValue() !== initialCode) {
          handleSave();
        }
      }, 30000); // 30秒自动保存

      return () => {
        clearInterval(autoSaveInterval);
        editorInstance.dispose();
      };
    }
  }, []);

  // 更新编辑器语言
  useEffect(() => {
    if (editor) {
      const model = editor.getModel();
      if (model) {
        monaco.editor.setModelLanguage(model, currentLanguage);
      }
    }
  }, [currentLanguage, editor]);

  // 更新编辑器设置
  useEffect(() => {
    if (editor) {
      editor.updateOptions(editorSettings);
    }
  }, [editorSettings, editor]);

  // 处理保存
  const handleSave = useCallback(() => {
    if (editor) {
      const value = editor.getValue();
      onSave?.(value);
      
      // 显示保存提示
      editor.trigger('keyboard', 'type', { text: '' });
      
      // 可以添加保存成功的视觉反馈
      const decorations = editor.deltaDecorations([], [{
        range: new monaco.Range(1, 1, 1, 1),
        options: {
          afterContentClassName: 'save-indicator'
        }
      }]);
      
      setTimeout(() => {
        editor.deltaDecorations(decorations, []);
      }, 1000);
    }
  }, [editor, onSave]);

  // 处理运行
  const handleRun = useCallback(() => {
    if (editor) {
      const value = editor.getValue();
      onRun?.(value, currentLanguage);
    }
  }, [editor, onRun, currentLanguage]);

  // 切换全屏
  const toggleFullscreen = useCallback(() => {
    setIsFullscreen(!isFullscreen);
    setTimeout(() => {
      if (editor) {
        editor.layout();
      }
    }, 100);
  }, [isFullscreen, editor]);

  // 格式化代码
  const formatCode = useCallback(() => {
    if (editor) {
      editor.getAction('editor.action.formatDocument').run();
    }
  }, [editor]);

  // 查找替换
  const toggleSearch = useCallback(() => {
    if (editor) {
      if (searchVisible) {
        editor.getAction('closeFindWidget').run();
      } else {
        editor.getAction('actions.find').run();
      }
      setSearchVisible(!searchVisible);
    }
  }, [editor, searchVisible]);

  // 获取语言图标
  const getLanguageIcon = (lang) => {
    const iconMap = {
      javascript: '🟨',
      typescript: '🔷',
      python: '🐍',
      java: '☕',
      cpp: '⚡',
      csharp: '🔷',
      go: '🐹',
      rust: '🦀',
      php: '🐘',
      ruby: '💎',
      html: '🌐',
      css: '🎨',
      json: '📋',
      markdown: '📝',
      sql: '🗃️',
      shell: '🐚'
    };
    return iconMap[lang] || '📄';
  };

  return (
    <div className={`monaco-editor-container ${isFullscreen ? 'fullscreen' : ''} ${className}`}>
      {/* 编辑器工具栏 */}
      <div className="editor-toolbar bg-gray-800 border-b border-gray-700 px-4 py-2 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          {/* 语言选择器 */}
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-400">Language:</span>
            <select
              value={currentLanguage}
              onChange={(e) => setCurrentLanguage(e.target.value)}
              className="bg-gray-700 text-white text-sm rounded px-2 py-1 border border-gray-600 focus:border-blue-500 focus:outline-none"
            >
              {SUPPORTED_LANGUAGES.map(lang => (
                <option key={lang.id} value={lang.id}>
                  {getLanguageIcon(lang.id)} {lang.name}
                </option>
              ))}
            </select>
          </div>

          {/* 文件操作 */}
          <div className="flex items-center space-x-2">
            <button
              onClick={handleSave}
              className="flex items-center space-x-1 px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition-colors"
              title="Save (Ctrl+S)"
            >
              <Save size={14} />
              <span>Save</span>
            </button>
            
            {!readOnly && (
              <button
                onClick={handleRun}
                className="flex items-center space-x-1 px-3 py-1 bg-green-600 hover:bg-green-700 text-white text-sm rounded transition-colors"
                title="Run (Ctrl+R)"
              >
                <Play size={14} />
                <span>Run</span>
              </button>
            )}
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* 编辑器操作 */}
          <button
            onClick={formatCode}
            className="p-1 text-gray-400 hover:text-white transition-colors"
            title="Format Code"
          >
            <Code size={16} />
          </button>
          
          <button
            onClick={toggleSearch}
            className="p-1 text-gray-400 hover:text-white transition-colors"
            title="Search (Ctrl+F)"
          >
            <Search size={16} />
          </button>
          
          <button
            onClick={toggleFullscreen}
            className="p-1 text-gray-400 hover:text-white transition-colors"
            title="Toggle Fullscreen"
          >
            {isFullscreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
          </button>
        </div>
      </div>

      {/* Monaco编辑器容器 */}
      <div 
        ref={containerRef}
        className="editor-container flex-1"
        style={{ height: isFullscreen ? 'calc(100vh - 120px)' : '600px' }}
      />

      {/* 状态栏 */}
      <div className="editor-statusbar bg-gray-800 border-t border-gray-700 px-4 py-1 flex items-center justify-between text-xs text-gray-400">
        <div className="flex items-center space-x-4">
          <span>Line {cursorPosition.line}, Column {cursorPosition.column}</span>
          {selectionInfo && <span>{selectionInfo}</span>}
          <span>{currentLanguage.toUpperCase()}</span>
        </div>
        
        <div className="flex items-center space-x-4">
          <span>UTF-8</span>
          <span>LF</span>
          <span>{code.length} chars</span>
          <span>{code.split('\n').length} lines</span>
        </div>
      </div>

      {/* 全屏样式 */}
      <style jsx>{`
        .monaco-editor-container {
          display: flex;
          flex-direction: column;
          height: 100%;
          background: #1e1e1e;
          border-radius: 8px;
          overflow: hidden;
          border: 1px solid #374151;
        }
        
        .monaco-editor-container.fullscreen {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          z-index: 1000;
          border-radius: 0;
          border: none;
        }
        
        .editor-container {
          position: relative;
        }
        
        .save-indicator::after {
          content: '✓ Saved';
          position: absolute;
          top: -20px;
          right: 0;
          background: #10b981;
          color: white;
          padding: 2px 8px;
          border-radius: 4px;
          font-size: 12px;
          animation: fadeInOut 1s ease-in-out;
        }
        
        @keyframes fadeInOut {
          0%, 100% { opacity: 0; }
          50% { opacity: 1; }
        }
        
        /* Monaco编辑器自定义样式 */
        .monaco-editor .margin {
          background-color: #1e1e1e !important;
        }
        
        .monaco-editor .monaco-editor-background {
          background-color: #1e1e1e !important;
        }
        
        .monaco-editor .current-line {
          background-color: #2d2d30 !important;
        }
        
        /* 滚动条样式 */
        .monaco-editor .monaco-scrollable-element > .scrollbar > .slider {
          background: rgba(121, 121, 121, 0.4) !important;
        }
        
        .monaco-editor .monaco-scrollable-element > .scrollbar > .slider:hover {
          background: rgba(121, 121, 121, 0.7) !important;
        }
        
        /* 建议框样式 */
        .monaco-editor .suggest-widget {
          background: #252526 !important;
          border: 1px solid #454545 !important;
        }
        
        .monaco-editor .suggest-widget .monaco-list .monaco-list-row {
          background: transparent !important;
        }
        
        .monaco-editor .suggest-widget .monaco-list .monaco-list-row:hover {
          background: #2a2d2e !important;
        }
        
        .monaco-editor .suggest-widget .monaco-list .monaco-list-row.focused {
          background: #094771 !important;
        }
      `}</style>
    </div>
  );
};

export default MonacoEditor;

