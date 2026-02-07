/**
 * ACE-Step Standalone - Frontend JavaScript
 */

console.log('ACE-Step app.js loaded');

// =============================================================================
// API Functions
// =============================================================================

/**
 * 音声URLをプロキシ経由にURLへ変換
 * CORSの問題を回避するため、ACE-Step APIの音声をバックエンド経由で取得
 */
function convertAudioUrl(url) {
    if (!url) return url;
    
    // 外部URL（ACE-Step API）の場合、プロキシ経由に変換
    try {
        const urlObj = new URL(url);
        // /v1/audio?path=... の形式の場合
        if (urlObj.pathname === '/v1/audio') {
            const path = urlObj.searchParams.get('path');
            if (path) {
                return `/api/audio?path=${encodeURIComponent(path)}`;
            }
        }
    } catch (e) {
        // 相対URLの場合はそのまま返す
    }
    
    return url;
}

/**
 * APIリクエストを送信
 */
async function apiRequest(endpoint, method = 'GET', data = null) {
    console.log(`API Request: ${method} ${endpoint}`, data);
    
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
        },
    };
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(endpoint, options);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('API Error:', errorText);
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('API Response:', result);
        return result;
    } catch (e) {
        console.error('API Request failed:', e);
        throw e;
    }
}

// =============================================================================
// UI Helper Functions
// =============================================================================

/**
 * ステータスメッセージを表示
 */
function showStatus(message, type = 'info') {
    const statusEl = document.getElementById('status-message');
    statusEl.textContent = message;
    statusEl.className = `status-message ${type}`;
    statusEl.style.display = 'block';
}

/**
 * ステータスメッセージを非表示
 */
function hideStatus() {
    document.getElementById('status-message').style.display = 'none';
}

/**
 * 進捗バーを表示/更新
 */
function showProgress(percent, text = '処理中...') {
    const container = document.getElementById('progress-container');
    const fill = document.getElementById('progress-fill');
    const textEl = document.getElementById('progress-text');
    
    container.style.display = 'block';
    fill.style.width = `${percent}%`;
    textEl.textContent = text;
}

/**
 * 進捗バーを非表示
 */
function hideProgress() {
    document.getElementById('progress-container').style.display = 'none';
}

// ビジュアライザー用のグローバル変数
let audioContext = null;
let analyser = null;
let dataArray = null;
let animationId = null;
let isVisualizerInitialized = false;

/**
 * オーディオプレイヤーを表示
 */
function showAudioPlayer(url, metadata = {}) {
    const playerSection = document.getElementById('player-section');
    const audio = document.getElementById('audio');
    const downloadBtn = document.getElementById('download-btn');
    
    audio.src = url;
    downloadBtn.href = url;
    
    // 再生セクションを表示
    playerSection.classList.add('visible');
    
    // スムーズにスクロール
    playerSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
    
    // ビジュアライザーを初期化
    initVisualizer();

    // 生成後は自動再生（ブラウザの制限で失敗する場合あり）
    setTimeout(() => {
        const playPromise = audio.play();
        if (playPromise && typeof playPromise.catch === 'function') {
            playPromise.catch(() => {
                showStatus('🎧 再生を開始できませんでした。再生ボタンを押してください。', 'info');
            });
        }
    }, 0);
}

/**
 * ビジュアライザーを初期化
 */
function initVisualizer() {
    const audio = document.getElementById('audio');
    
    if (isVisualizerInitialized) return;
    
    // 再生開始時にAudioContextを作成（ユーザー操作後のみ許可）
    audio.addEventListener('play', () => {
        if (!audioContext) {
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            analyser = audioContext.createAnalyser();
            analyser.fftSize = 256;
            
            const source = audioContext.createMediaElementSource(audio);
            source.connect(analyser);
            analyser.connect(audioContext.destination);
            
            const bufferLength = analyser.frequencyBinCount;
            dataArray = new Uint8Array(bufferLength);
        }
        
        if (audioContext.state === 'suspended') {
            audioContext.resume();
        }
        
        drawVisualizer();
    });
    
    audio.addEventListener('pause', () => {
        if (animationId) {
            cancelAnimationFrame(animationId);
            animationId = null;
        }
    });
    
    audio.addEventListener('ended', () => {
        if (animationId) {
            cancelAnimationFrame(animationId);
            animationId = null;
        }
        clearVisualizer();
    });
    
    isVisualizerInitialized = true;
}

/**
 * ビジュアライザーを描画
 */
function drawVisualizer() {
    const canvas = document.getElementById('visualizer');
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    
    function draw() {
        animationId = requestAnimationFrame(draw);
        
        analyser.getByteFrequencyData(dataArray);
        
        // 背景をクリア（グラデーション）
        const gradient = ctx.createLinearGradient(0, 0, 0, height);
        gradient.addColorStop(0, '#1a1a2e');
        gradient.addColorStop(1, '#16213e');
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, width, height);
        
        const barCount = 64;
        const barWidth = (width / barCount) * 0.8;
        const barGap = (width / barCount) * 0.2;
        
        for (let i = 0; i < barCount; i++) {
            const dataIndex = Math.floor(i * dataArray.length / barCount);
            const barHeight = (dataArray[dataIndex] / 255) * height * 0.9;
            
            const x = i * (barWidth + barGap);
            const y = height - barHeight;
            
            // カラフルなグラデーション
            const hue = (i / barCount) * 360;
            const saturation = 80 + (dataArray[dataIndex] / 255) * 20;
            const lightness = 50 + (dataArray[dataIndex] / 255) * 20;
            
            // グロー効果
            ctx.shadowBlur = 15;
            ctx.shadowColor = `hsl(${hue}, ${saturation}%, ${lightness}%)`;
            
            // バーを描画
            const barGradient = ctx.createLinearGradient(x, y, x, height);
            barGradient.addColorStop(0, `hsl(${hue}, ${saturation}%, ${lightness}%)`);  
            barGradient.addColorStop(1, `hsl(${hue}, ${saturation}%, ${lightness - 20}%)`);
            
            ctx.fillStyle = barGradient;
            ctx.beginPath();
            ctx.roundRect(x, y, barWidth, barHeight, 3);
            ctx.fill();
        }
        
        ctx.shadowBlur = 0;
    }
    
    draw();
}

/**
 * ビジュアライザーをクリア
 */
function clearVisualizer() {
    const canvas = document.getElementById('visualizer');
    const ctx = canvas.getContext('2d');
    
    const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
    gradient.addColorStop(0, '#1a1a2e');
    gradient.addColorStop(1, '#16213e');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
}

/**
 * ボタンを無効化
 */
function disableButton(id, loading = true) {
    const btn = document.getElementById(id);
    btn.disabled = true;
    if (loading) {
        btn.dataset.originalText = btn.innerHTML;
        btn.innerHTML = '<span class="spinner"></span> 処理中...';
    }
}

/**
 * ボタンを有効化
 */
function enableButton(id) {
    const btn = document.getElementById(id);
    btn.disabled = false;
    if (btn.dataset.originalText) {
        btn.innerHTML = btn.dataset.originalText;
    }
}

/**
 * 構造タグを挿入
 */
function insertTag(tag) {
    const textarea = document.getElementById('lyrics');
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const text = textarea.value;
    
    textarea.value = text.substring(0, start) + tag + '\n' + text.substring(end);
    textarea.focus();
    textarea.selectionStart = textarea.selectionEnd = start + tag.length + 1;
}

/**
 * ジャンルを追加
 */
function addGenre(genre) {
    const promptEl = document.getElementById('prompt');
    const current = promptEl.value.trim();
    
    if (current) {
        promptEl.value = current + ', ' + genre;
    } else {
        promptEl.value = genre;
    }
}

/**
 * アコーディオンをトグル
 */
function toggleAccordion(id) {
    const accordion = document.getElementById(id);
    accordion.classList.toggle('open');
}

/**
 * フォームをリセット
 */
function resetForm() {
    document.getElementById('theme').value = '';
    document.getElementById('lyrics').value = '';
    document.getElementById('prompt').value = '';
    document.getElementById('audio_duration').value = 150;
    document.getElementById('bpm').value = 120;
    document.getElementById('inference_steps').value = 60;
    document.getElementById('guidance_scale').value = 3.0;
    document.getElementById('key_scale').value = '';
    document.getElementById('seed').value = '';
    
    hideStatus();
    hideProgress();
    
    // 再生セクションを非表示
    document.getElementById('player-section').classList.remove('visible');
    
    // 音声を停止
    const audio = document.getElementById('audio');
    audio.pause();
    audio.src = '';
}

// =============================================================================
// Main Functions
// =============================================================================

/**
 * AI作詞
 */
async function generateLyrics() {
    console.log('generateLyrics called');
    const theme = document.getElementById('theme').value.trim();
    console.log('Theme:', theme);
    
    if (!theme) {
        showStatus('テーマを入力してください', 'error');
        return;
    }
    
    const btn = document.getElementById('lyrics-btn');
    const originalText = btn.innerHTML;
    
    try {
        // ボタンをローディング状態に
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span> 生成中...';
        showStatus('歌詞を生成中...（LLMに問い合わせ中）', 'info');
        
        const language = document.getElementById('language').value;
        const languageMap = {
            'ja': 'Japanese',
            'en': 'English',
            'zh': 'Chinese',
            'ko': 'Korean',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German'
        };
        
        const result = await apiRequest('/api/lyrics', 'POST', {
            theme: theme,
            genre: document.getElementById('prompt').value,
            language: languageMap[language] || 'Japanese'
        });
        
        if (result.success) {
            document.getElementById('lyrics').value = result.lyrics;
            
            // 推奨秒数を設定
            if (result.recommended_duration) {
                const duration = Math.min(180, Math.max(10, result.recommended_duration));
                document.getElementById('audio_duration').value = duration;
                const durationValueEl = document.getElementById('duration_value');
                if (durationValueEl) {
                    durationValueEl.textContent = duration;
                }
            }
            
            showStatus('✅ 歌詞を生成しました！', 'success');
        } else {
            showStatus('❌ 歌詞生成に失敗: ' + (result.error || '不明なエラー'), 'error');
        }
    } catch (e) {
        showStatus('❌ エラー: ' + e.message, 'error');
    } finally {
        // ボタンを元に戻す
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

/**
 * タグ生成
 */
async function generateTags() {
    const theme = document.getElementById('theme').value.trim();
    const lyrics = document.getElementById('lyrics').value.trim();
    
    if (!theme && !lyrics) {
        showStatus('テーマまたは歌詞を入力してください', 'error');
        return;
    }
    
    const btn = document.getElementById('tags-btn');
    const originalText = btn.innerHTML;
    
    try {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span> 生成中...';
        showStatus('タグを生成中...（LLMに問い合わせ中）', 'info');
        
        const result = await apiRequest('/api/tags', 'POST', {
            theme: theme,
            lyrics: lyrics,
            language: 'Japanese'
        });
        
        if (result.success) {
            // タグを設定
            const tags = [];
            if (result.genre) tags.push(result.genre);
            if (result.tags) tags.push(result.tags);
            document.getElementById('prompt').value = tags.join(', ');
            
            // BPMを設定
            if (result.bpm) {
                document.getElementById('bpm').value = result.bpm;
            }
            
            // 調を設定
            if (result.key_scale) {
                document.getElementById('key_scale').value = result.key_scale;
            }
            
            showStatus('✅ タグを生成しました！', 'success');
        } else {
            showStatus('❌ タグ生成に失敗: ' + (result.error || '不明なエラー'), 'error');
        }
    } catch (e) {
        showStatus('❌ エラー: ' + e.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

/**
 * 一括生成（AUTO）
 */
async function autoGenerate() {
    const theme = document.getElementById('theme').value.trim();
    
    if (!theme) {
        showStatus('テーマを入力してください', 'error');
        return;
    }
    
    const btn = document.getElementById('auto-btn');
    const originalText = btn.innerHTML;
    
    try {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span> 一括生成中...';
        showStatus('歌詞とタグを生成中...（LLMに問い合わせ中、30秒〜1分かかります）', 'info');
        
        const language = document.getElementById('language').value;
        const languageMap = {
            'ja': 'Japanese',
            'en': 'English',
            'zh': 'Chinese',
            'ko': 'Korean',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German'
        };
        
        const result = await apiRequest('/api/full_generate', 'POST', {
            theme: theme,
            genre: document.getElementById('prompt').value,
            language: languageMap[language] || 'Japanese'
        });
        
        if (result.success) {
            // 歌詞を設定
            document.getElementById('lyrics').value = result.lyrics;
            
            // タグを設定
            const tags = [];
            if (result.genre) tags.push(result.genre);
            if (result.tags) tags.push(result.tags);
            document.getElementById('prompt').value = tags.join(', ');
            
            // 推奨秒数を設定
            if (result.recommended_duration) {
                const duration = Math.min(300, Math.max(10, result.recommended_duration));
                document.getElementById('audio_duration').value = duration;
            }
            
            // BPMを設定
            if (result.bpm) {
                document.getElementById('bpm').value = result.bpm;
            }
            
            // 調を設定
            if (result.key_scale) {
                document.getElementById('key_scale').value = result.key_scale;
            }
            
            showStatus('✅ 歌詞とタグを生成しました！「音楽を生成」をクリックして音楽を作成できます', 'success');
        } else {
            showStatus('❌ 生成に失敗: ' + (result.error || '不明なエラー'), 'error');
        }
    } catch (e) {
        showStatus('❌ エラー: ' + e.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

/**
 * 音楽生成
 */
async function generateMusic() {
    const prompt = document.getElementById('prompt').value.trim();
    const lyrics = document.getElementById('lyrics').value.trim();
    
    if (!prompt && !lyrics) {
        showStatus('タグまたは歌詞を入力してください', 'error');
        return;
    }
    
    try {
        disableButton('generate-btn');
        hideStatus();
        showProgress(0, 'タスクを作成中...');
        
        // パラメータを収集
        const params = {
            prompt: prompt,
            lyrics: lyrics,
            thinking: document.getElementById('thinking').checked,
            vocal_language: document.getElementById('language').value,
            audio_duration: parseInt(document.getElementById('audio_duration').value),
            bpm: parseInt(document.getElementById('bpm').value),
            inference_steps: parseInt(document.getElementById('inference_steps').value),
            guidance_scale: parseFloat(document.getElementById('guidance_scale').value),
            time_signature: document.getElementById('time_signature').value,
            batch_size: parseInt(document.getElementById('batch_size').value),
            audio_format: document.getElementById('audio_format').value,
        };
        
        // キースケール
        const keyScale = document.getElementById('key_scale').value;
        if (keyScale) {
            params.key_scale = keyScale;
        }
        
        // シード
        const seed = document.getElementById('seed').value;
        if (seed) {
            params.seed = parseInt(seed);
        }
        
        // タスク作成
        const createResult = await apiRequest('/api/generate', 'POST', params);
        const taskId = createResult.task_id;
        
        if (!taskId) {
            throw new Error('タスクの作成に失敗しました');
        }
        
        showProgress(10, 'タスク作成完了。生成中...');
        
        // ポーリングで完了を待つ
        const maxPolls = 300;  // 5分（1秒間隔）
        let polls = 0;
        
        while (polls < maxPolls) {
            await sleep(1000);
            polls++;
            
            const statusResult = await apiRequest(`/api/status/${taskId}`);
            
            if (statusResult.status === 1) {
                // 成功
                showProgress(100, '生成完了！');
                
                if (statusResult.results && statusResult.results.length > 0) {
                    const result = statusResult.results[0];
                    // CORS回避のため、プロキシ経由のURLに変換
                    const audioUrl = convertAudioUrl(result.url);
                    showAudioPlayer(audioUrl, result.metas || {});
                    showStatus('音楽を生成しました！', 'success');
                }
                
                hideProgress();
                enableButton('generate-btn');
                return;
            } else if (statusResult.status === 2) {
                // 失敗
                throw new Error(statusResult.error || '生成に失敗しました');
            }
            
            // 進捗更新
            const progress = Math.min(90, 10 + (polls / maxPolls) * 80);
            showProgress(progress, `生成中... (${polls}秒経過)`);
        }
        
        throw new Error('タイムアウト: 生成に時間がかかりすぎています');
        
    } catch (e) {
        showStatus('エラー: ' + e.message, 'error');
        hideProgress();
        enableButton('generate-btn');
    }
}

/**
 * スリープ関数
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// =============================================================================
// Initialization
// =============================================================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('ACE-Step Standalone initialized');
    
    // カスタムリサイズハンドルの初期化
    initResizeHandles();
    
    // サーバー情報を取得して表示
    loadServerInfo();
});

/**
 * サーバー情報（モデル・統計）を取得して表示
 */
async function loadServerInfo() {
    try {
        // モデル情報を取得
        const modelResult = await apiRequest('/api/models');
        if (modelResult.success) {
            const modelName = modelResult.default_model || 'unknown';
            const modelDisplay = modelName.replace('acestep-', '').replace('-', ' ');
            const isTurbo = modelName.includes('turbo');
            
            const modelEl = document.getElementById('model-info');
            modelEl.innerHTML = `🤖 モデル: <strong>${modelDisplay}</strong>${isTurbo ? ' ⚡' : ''}`;
            modelEl.title = `フルネーム: ${modelName}${isTurbo ? '\nTurboモデル: STEP 8推奨' : '\nBaseモデル: STEP 60推奨'}`;
            
            // Turboモデルの場合、STEPのデフォルトを調整
            if (isTurbo) {
                const stepInput = document.getElementById('inference_steps');
                if (stepInput && stepInput.value == 60) {
                    stepInput.value = 8;
                    stepInput.title = '推論ステップ数（Turboモデル: 8推奨）';
                }
            }
        } else {
            document.getElementById('model-info').innerHTML = '🤖 モデル: <span style="color: var(--error-color);">接続エラー</span>';
        }
        
        // 統計情報を取得
        const statsResult = await apiRequest('/api/stats');
        if (statsResult.success) {
            document.getElementById('queue-info').innerHTML = `📊 キュー: <strong>${statsResult.queue_size}</strong>`;
            const avgTime = statsResult.avg_job_seconds ? statsResult.avg_job_seconds.toFixed(1) : '-';
            document.getElementById('avg-time-info').innerHTML = `⏱️ 平均: <strong>${avgTime}秒</strong>`;
        }
    } catch (e) {
        console.error('Failed to load server info:', e);
        document.getElementById('model-info').innerHTML = '🤖 モデル: <span style="color: var(--error-color);">接続エラー</span>';
    }
}

/**
 * カスタムリサイズハンドルを初期化
 */
function initResizeHandles() {
    const resizeHandles = document.querySelectorAll('.resize-handle');
    
    resizeHandles.forEach(handle => {
        const container = handle.closest('.textarea-container');
        const textarea = container.querySelector('textarea');
        
        if (!textarea) return;
        
        let isResizing = false;
        let startY = 0;
        let startHeight = 0;
        
        handle.addEventListener('mousedown', (e) => {
            isResizing = true;
            startY = e.clientY;
            startHeight = textarea.offsetHeight;
            document.body.style.cursor = 'ns-resize';
            document.body.style.userSelect = 'none';
            e.preventDefault();
        });
        
        document.addEventListener('mousemove', (e) => {
            if (!isResizing) return;
            
            const deltaY = e.clientY - startY;
            const newHeight = Math.max(150, startHeight + deltaY);
            textarea.style.height = newHeight + 'px';
        });
        
        document.addEventListener('mouseup', () => {
            if (isResizing) {
                isResizing = false;
                document.body.style.cursor = '';
                document.body.style.userSelect = '';
            }
        });
        
        // タッチ対応
        handle.addEventListener('touchstart', (e) => {
            isResizing = true;
            startY = e.touches[0].clientY;
            startHeight = textarea.offsetHeight;
            e.preventDefault();
        });
        
        document.addEventListener('touchmove', (e) => {
            if (!isResizing) return;
            
            const deltaY = e.touches[0].clientY - startY;
            const newHeight = Math.max(150, startHeight + deltaY);
            textarea.style.height = newHeight + 'px';
        });
        
        document.addEventListener('touchend', () => {
            isResizing = false;
        });
    });
}
