#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""QQ照片批量下载工具 v4.0"""

import os, re, requests
from pathlib import Path
from threading import Thread
import customtkinter as ctk
from tkinter import filedialog, messagebox

# 外观设置
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


def calc_g_tk(skey):
    p = 5381
    for c in skey:
        p += (p << 5) + ord(c)
    return p & 2147483647


class QQPhotoDownloader:
    def __init__(self, cookie, qq_number):
        self.cookie = cookie
        self.qq_number = qq_number
        m = re.search(r'p_skey=([^;]+)', cookie)
        self.g_tk = calc_g_tk(m.group(1)) if m else None
        self.headers = {
            'Cookie': cookie,
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15',
        }

    def get_album_list(self):
        """获取相册列表 - mobile.qzone.qq.com"""
        if not self.g_tk:
            return None, "Cookie中未找到p_skey"
        
        url = f"https://mobile.qzone.qq.com/list?g_tk={self.g_tk}&format=json&list_type=album&action=0&res_uin={self.qq_number}&count=99"
        try:
            r = requests.get(url, headers=self.headers, timeout=15)
            if r.status_code != 200:
                return None, f"HTTP {r.status_code}"
            
            d = r.json()
            if d.get('code') != 0:
                return None, f"API错误: {d.get('message', '?')}"
            
            # 解析vFeeds中的相册
            albums = []
            seen_ids = set()
            data = d.get('data', {})
            
            for feed in data.get('vFeeds', []):
                pic = feed.get('pic', {})
                aid = pic.get('albumid', '')
                if aid and aid not in seen_ids:
                    seen_ids.add(aid)
                    albums.append({
                        'id': aid,
                        'name': pic.get('albumname', '?'),
                        'count': pic.get('albumnum', 0)
                    })
            
            # 可能还有更多
            attach = data.get('attach_info', '')
            has_more = data.get('has_more', 0)
            
            if has_more and attach:
                # 继续获取
                while has_more:
                    url2 = f"https://mobile.qzone.qq.com/list?g_tk={self.g_tk}&format=json&list_type=album&action=0&res_uin={self.qq_number}&count=99&attach_info={attach}"
                    r2 = requests.get(url2, headers=self.headers, timeout=15)
                    d2 = r2.json()
                    if d2.get('code') != 0:
                        break
                    data2 = d2.get('data', {})
                    for feed in data2.get('vFeeds', []):
                        pic = feed.get('pic', {})
                        aid = pic.get('albumid', '')
                        if aid and aid not in seen_ids:
                            seen_ids.add(aid)
                            albums.append({
                                'id': aid,
                                'name': pic.get('albumname', '?'),
                                'count': pic.get('albumnum', 0)
                            })
                    attach = data2.get('attach_info', '')
                    has_more = data2.get('has_more', 0)
            
            return albums, None
        except Exception as e:
            return None, str(e)

    def get_photo_list(self, album_id):
        """获取照片列表 - getPhotoList2"""
        if not self.g_tk:
            return None, "g_tk无效"
        
        url = f"https://h5.qzone.qq.com/webapp/json/mqzone_photo/getPhotoList2?g_tk={self.g_tk}&format=json&uin={self.qq_number}&albumid={album_id}&photocount=2000"
        try:
            r = requests.get(url, headers=self.headers, timeout=30)
            if r.status_code != 200:
                return None, f"HTTP {r.status_code}"
            
            d = r.json()
            if d.get('code') != 0:
                return None, f"API错误: {d.get('message', '?')}"
            
            # data.photos 是按时间戳分组的字典
            photos_data = d.get('data', {}).get('photos', {})
            photos = []
            
            for ts, group in photos_data.items():
                if isinstance(group, list):
                    for p in group:
                        # 字段'1'是原图，字段'11'是缩略图
                        url_info = p.get('1') or p.get('11') or {}
                        raw_url = url_info.get('url', '')
                        if raw_url:
                            photos.append({
                                'url': raw_url,
                                'width': url_info.get('width', 0),
                                'height': url_info.get('height', 0),
                                'name': p.get('picname', ''),
                                'uploadTime': p.get('uploadUin', 0)
                            })
            
            return photos, None
        except Exception as e:
            return None, str(e)

    def download_photo(self, url, save_path, filename):
        """下载照片"""
        try:
            r = requests.get(url, headers=self.headers, timeout=30, allow_redirects=True)
            if r.status_code == 200 and len(r.content) > 1024:
                with open(Path(save_path) / filename, 'wb') as f:
                    f.write(r.content)
                return True
        except:
            pass
        return False


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("QQ照片批量下载工具 v4.0")
        self.geometry("800x750")
        self.downloader = None
        self.albums = []
        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(self, text="使用说明：\n1. 打开 qzone.qq.com 登录\n2. F12复制Cookie粘贴到下面\n3. 获取相册→选择→下载",
                    justify="left", font=("", 13)).pack(pady=12, padx=15, anchor="w")

        qf = ctk.CTkFrame(self)
        qf.pack(pady=5, padx=15, fill="x")
        ctk.CTkLabel(qf, text="QQ号:", font=("", 13)).pack(side="left", padx=5)
        self.qq_entry = ctk.CTkEntry(qf, width=160, font=("", 13))
        self.qq_entry.pack(side="left", padx=5)

        ctk.CTkLabel(self, text="Cookie:", font=("", 13)).pack(pady=(10, 0), padx=15, anchor="w")
        self.cookie_text = ctk.CTkTextbox(self, width=750, height=90, font=("", 11))
        self.cookie_text.pack(pady=5, padx=15, fill="x")

        bf = ctk.CTkFrame(self)
        bf.pack(pady=10)
        ctk.CTkButton(bf, text="获取相册列表", command=self._get_albums,
                     width=140, height=38, font=("", 13)).pack(side="left", padx=8)
        ctk.CTkButton(bf, text="开始下载", command=self._start_download,
                     width=160, height=38, font=("", 13),
                     fg_color="#1a73e8").pack(side="left", padx=8)

        pf = ctk.CTkFrame(self)
        pf.pack(pady=5, padx=15, fill="x")
        ctk.CTkLabel(pf, text="保存:", font=("", 13)).pack(side="left", padx=5)
        self.path_entry = ctk.CTkEntry(pf, font=("", 12))
        self.path_entry.insert(0, str(Path.home() / "Downloads" / "QQ照片"))
        self.path_entry.pack(side="left", padx=5, fill="x", expand=True)
        ctk.CTkButton(pf, text="选择", command=self._select_path,
                     width=60, font=("", 12)).pack(side="left", padx=5)

        ctk.CTkLabel(self, text="相册列表:", font=("", 14, "bold")).pack(pady=(10, 0), padx=15, anchor="w")
        self.album_listbox = ctk.CTkTextbox(self, width=750, height=220, font=("", 12))
        self.album_listbox.pack(pady=5, padx=15, fill="both", expand=True)

        ctk.CTkLabel(self, text="日志:", font=("", 14, "bold")).pack(pady=(8, 0), padx=15, anchor="w")
        self.log_text = ctk.CTkTextbox(self, width=750, height=110, font=("", 11))
        self.log_text.pack(pady=5, padx=15, fill="x")

    def _select_path(self):
        p = filedialog.askdirectory()
        if p:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, p)

    def _log(self, msg):
        self.log_text.insert("end", f"{msg}\n")
        self.log_text.see("end")
        self.update_idletasks()

    def _get_albums(self):
        qq = self.qq_entry.get().strip()
        cookie = self.cookie_text.get("1.0", "end").strip()
        if not qq or not cookie:
            messagebox.showerror("错误", "请输入QQ号和Cookie")
            return
        self._log("正在获取相册列表...")

        def run():
            self.downloader = QQPhotoDownloader(cookie, qq)
            albums, err = self.downloader.get_album_list()
            if err:
                self._log(f"❌ {err}")
                messagebox.showerror("错误", err)
                return
            if not albums:
                self._log("❌ 未找到相册")
                return
            self.albums = albums
            self.album_listbox.delete("1.0", "end")
            for i, a in enumerate(albums):
                self.album_listbox.insert("end", f"{i+1}. {a['name']} ({a['count']}张)\n")
            self._log(f"✅ 找到 {len(albums)} 个相册")

        Thread(target=run, daemon=True).start()

    def _start_download(self):
        if not self.downloader or not self.albums:
            messagebox.showerror("错误", "请先获取相册列表")
            return
        
        sp = self.path_entry.get().strip()
        Path(sp).mkdir(parents=True, exist_ok=True)
        self._log(f"开始下载 {len(self.albums)} 个相册...")

        def run():
            tp = ts = 0
            for i, a in enumerate(self.albums):
                name = a['name']
                aid = a['id']
                ap = Path(sp) / f"{i+1}_{name}"
                ap.mkdir(parents=True, exist_ok=True)
                self._log(f"[{i+1}/{len(self.albums)}] {name}...")

                photos, err = self.downloader.get_photo_list(aid)
                if err:
                    self._log(f"  ❌ {err}")
                    continue
                if not photos:
                    self._log("  ⚠️ 无照片")
                    continue

                ok = 0
                for j, p in enumerate(photos):
                    url = p.get('url', '')
                    if not url:
                        continue
                    filename = p.get('name', f"photo_{j+1:04d}.jpg")
                    if not filename.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        filename += '.jpg'
                    
                    if self.downloader.download_photo(url, ap, filename):
                        ok += 1
                    if (j + 1) % 20 == 0:
                        self._log(f"  {j+1}/{len(photos)}")
                
                self._log(f"  ✅ {ok}/{len(photos)}")
                tp += len(photos)
                ts += ok
            
            self._log(f"\n🎉 完成! {ts}/{tp}")
            messagebox.showinfo("完成", f"下载完成: {ts}/{tp}")

        Thread(target=run, daemon=True).start()


if __name__ == "__main__":
    app = App()
    app.mainloop()
