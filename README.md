# 澳洲监视器 Lite

当前采用单仓库结构：

- `C:\work\ozmonitor`: 内容生成 + 前端站点
- 前端放在子目录 `site/`

## 目录说明

- `scripts/generate_update.py`: 抓取并生成监控数据
- `scripts/publish_update.py`: 生成数据并同步到 `site/data/latest.json` 后自动 push
- `data/latest.json`: 本地生成结果
- `data/history.json`: 本地历史快照
- `site/index.html` / `site/style.css` / `site/app.js`: 前端页面
- `site/data/latest.json`: 前端读取的数据
- `.github/workflows/deploy-pages.yml`: Pages 自动部署

## 1) 初始化仓库

```powershell
cd C:\work\ozmonitor
git init -b main
git add .
git commit -m "init ozmonitor"
git remote add origin https://github.com/<yourname>/<repo>.git
git push -u origin main
```

然后在 GitHub 仓库中开启 `Settings -> Pages -> GitHub Actions`，部署目录由 workflow 指向 `./site`。

## 2) 本地更新并推送

```powershell
cd C:\work\ozmonitor
python scripts/publish_update.py
```

这个脚本会：

1. 生成 `C:\work\ozmonitor\data\latest.json`
2. 同步到 `C:\work\ozmonitor\site\data\latest.json`
3. 在当前仓库自动 `git commit` + `git push`

## 3) Windows 定时任务（每 30 分钟）

```powershell
schtasks /Create /SC MINUTE /MO 30 /TN "OzMonitorLite" /TR "powershell -NoProfile -ExecutionPolicy Bypass -Command \"cd /d C:\work\ozmonitor; python scripts/publish_update.py\"" /F
```

## 数据来源

- 澳大利亚新闻：ABC RSS
- 布里斯班天气：Open-Meteo
- 汇率：ER-API
