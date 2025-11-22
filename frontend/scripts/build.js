/**
 * SkyCamOS - Script de Build
 * Gera build de producao da aplicacao
 */

import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, '..');

// Diretorios
const publicDir = path.join(rootDir, 'public');
const srcDir = path.join(rootDir, 'src');
const distDir = path.join(rootDir, 'dist');

/**
 * Limpar diretorio de build
 */
function cleanDist() {
    console.log('[Build] Limpando diretorio dist...');
    if (fs.existsSync(distDir)) {
        fs.rmSync(distDir, { recursive: true });
    }
    fs.mkdirSync(distDir, { recursive: true });
}

/**
 * Copiar arquivos publicos
 */
function copyPublicFiles() {
    console.log('[Build] Copiando arquivos publicos...');

    const copyRecursive = (src, dest) => {
        const stat = fs.statSync(src);

        if (stat.isDirectory()) {
            if (!fs.existsSync(dest)) {
                fs.mkdirSync(dest, { recursive: true });
            }

            fs.readdirSync(src).forEach(file => {
                copyRecursive(path.join(src, file), path.join(dest, file));
            });
        } else {
            fs.copyFileSync(src, dest);
        }
    };

    // Copiar todo o conteudo de public para dist
    fs.readdirSync(publicDir).forEach(file => {
        const srcPath = path.join(publicDir, file);
        const destPath = path.join(distDir, file);
        copyRecursive(srcPath, destPath);
    });
}

/**
 * Copiar diretorio src para dist
 */
function copySrcFiles() {
    console.log('[Build] Copiando arquivos src...');

    const srcDestDir = path.join(distDir, 'src');

    const copyRecursive = (src, dest) => {
        const stat = fs.statSync(src);

        if (stat.isDirectory()) {
            if (!fs.existsSync(dest)) {
                fs.mkdirSync(dest, { recursive: true });
            }

            fs.readdirSync(src).forEach(file => {
                copyRecursive(path.join(src, file), path.join(dest, file));
            });
        } else {
            fs.copyFileSync(src, dest);
        }
    };

    copyRecursive(srcDir, srcDestDir);
}

/**
 * Minificar arquivos JS (opcional - requer esbuild)
 */
function minifyJS() {
    console.log('[Build] Minificando arquivos JavaScript...');

    try {
        // Verificar se esbuild esta disponivel
        const files = [];

        const findJSFiles = (dir) => {
            fs.readdirSync(dir).forEach(file => {
                const filePath = path.join(dir, file);
                const stat = fs.statSync(filePath);

                if (stat.isDirectory()) {
                    findJSFiles(filePath);
                } else if (file.endsWith('.js')) {
                    files.push(filePath);
                }
            });
        };

        findJSFiles(path.join(distDir, 'src'));

        files.forEach(file => {
            try {
                execSync(`npx esbuild "${file}" --minify --outfile="${file}" --allow-overwrite`, {
                    stdio: 'pipe'
                });
            } catch (e) {
                console.warn(`[Build] Aviso: nao foi possivel minificar ${file}`);
            }
        });

        console.log(`[Build] ${files.length} arquivos processados`);
    } catch (error) {
        console.warn('[Build] Aviso: esbuild nao disponivel, pulando minificacao');
    }
}

/**
 * Minificar arquivos CSS
 */
function minifyCSS() {
    console.log('[Build] Minificando arquivos CSS...');

    const cssDir = path.join(distDir, 'src', 'styles');

    if (!fs.existsSync(cssDir)) return;

    fs.readdirSync(cssDir).forEach(file => {
        if (file.endsWith('.css')) {
            const filePath = path.join(cssDir, file);
            let content = fs.readFileSync(filePath, 'utf-8');

            // Minificacao simples
            content = content
                .replace(/\/\*[\s\S]*?\*\//g, '') // Remover comentarios
                .replace(/\s+/g, ' ') // Reduzir espacos
                .replace(/\s*{\s*/g, '{')
                .replace(/\s*}\s*/g, '}')
                .replace(/\s*;\s*/g, ';')
                .replace(/\s*:\s*/g, ':')
                .replace(/\s*,\s*/g, ',')
                .trim();

            fs.writeFileSync(filePath, content);
        }
    });
}

/**
 * Gerar hash para cache busting
 */
function generateBuildInfo() {
    console.log('[Build] Gerando informacoes de build...');

    const buildInfo = {
        version: process.env.npm_package_version || '1.0.0',
        buildTime: new Date().toISOString(),
        hash: Date.now().toString(36)
    };

    fs.writeFileSync(
        path.join(distDir, 'build-info.json'),
        JSON.stringify(buildInfo, null, 2)
    );

    console.log(`[Build] Versao: ${buildInfo.version}, Hash: ${buildInfo.hash}`);
}

/**
 * Executar build
 */
function build() {
    console.log('='.repeat(50));
    console.log('[Build] Iniciando build de producao...');
    console.log('='.repeat(50));

    const startTime = Date.now();

    try {
        cleanDist();
        copyPublicFiles();
        copySrcFiles();
        minifyCSS();
        minifyJS();
        generateBuildInfo();

        const duration = ((Date.now() - startTime) / 1000).toFixed(2);

        console.log('='.repeat(50));
        console.log(`[Build] Build concluido em ${duration}s`);
        console.log(`[Build] Output: ${distDir}`);
        console.log('='.repeat(50));

    } catch (error) {
        console.error('[Build] Erro durante o build:', error);
        process.exit(1);
    }
}

// Executar
build();
