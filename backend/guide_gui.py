import customtkinter as ctk
from PIL import ImageGrab
import os
import tkinter.messagebox

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class GuideApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("JamDeck - Jammers İçin Kılavuz")
        self.geometry("720x820")
        self.resizable(False, False)

        # Main frame
        self.main_frame = ctk.CTkFrame(self, fg_color="#141414", corner_radius=15)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        self.title_label = ctk.CTkLabel(self.main_frame, text="🎮 JAMDECK TESLİM KILAVUZU", 
                                        font=ctk.CTkFont(size=28, weight="bold"),
                                        text_color="#00f2ff")
        self.title_label.pack(pady=(30, 10))

        self.subtitle_label = ctk.CTkLabel(self.main_frame, text="Oyununuzun jüri sisteminde sorunsuz çalışması için altın kurallar!", 
                                           font=ctk.CTkFont(size=14, slant="italic"))
        self.subtitle_label.pack(pady=(0, 20))

        # Content Frame
        self.content_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=30)

        # Rules
        self.add_rule("1. name.txt İLE İSMİNİZİ BELİRLEYİN", 
                      "Oyun .exe dosyanızın bulunduğu klasörün içine 'name.txt' adında bir dosya oluşturun.\n"
                      "1. Satıra TAKIM İSMİNİZİ\n"
                      "2. Satıra OYUN İSMİNİZİ yazın.\n"
                      "Bu sayede oyununuz sistemde tam istediğiniz isimle görünür.", 
                      "#ff2bd6")
        
        self.add_rule("2. OYUN MOTORU UYARILARI", 
                      "• UNITY: Build aldıktan sonra oluşan .exe dosyanızın ismini ASLA değiştirmeyin!\n"
                      "• GODOT: Oluşturulan .exe ve .pck dosyalarının isimlerinin AYNI olduğundan emin olun.\n", 
                      "#ffc107")

        self.add_rule("3. SADECE WINDOWS (.exe) YÜKLEYİN", 
                      "Jüri oyunları Windows üzerinden oynayacaktır. Lütfen sadece Mac (.app)\n"
                      "veya sadece Web (HTML) dosyaları yüklemeyin. Oyun klasörünüzde kesinlikle\n"
                      "bir .exe dosyası bulunmalıdır. Aksi halde oyununuz BOZUK işaretlenir.", 
                      "#f44336")

        self.add_rule("4. İÇ İÇE ZİP YAPMAYIN", 
                      "Oyununuzu sıkıştırırken klasörü klasörün içine, onu da rar'ın içine koymayın.\n"
                      "Mümkün olduğunca sade, klasör yapısı bozulmamış tek bir .zip dosyası yükleyin.", 
                      "#4caf50")

        # Export Button
        self.export_btn = ctk.CTkButton(self, text="📥 PNG Olarak Kaydet (Discord'da Paylaşmak İçin)",
                                        font=ctk.CTkFont(size=15, weight="bold"),
                                        fg_color="#00f2ff", text_color="#000000",
                                        hover_color="#00c8d6", height=45,
                                        command=self.export_png)
        self.export_btn.pack(pady=(0, 20), padx=20, fill="x")

    def add_rule(self, title, text, color):
        frame = ctk.CTkFrame(self.content_frame, fg_color="#1e1e1e", corner_radius=10, border_width=2, border_color=color)
        frame.pack(fill="x", pady=8)
        
        lbl_title = ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=16, weight="bold"), text_color=color)
        lbl_title.pack(anchor="w", padx=15, pady=(10, 5))
        
        lbl_text = ctk.CTkLabel(frame, text=text, font=ctk.CTkFont(size=13), justify="left", text_color="#e0e0e0")
        lbl_text.pack(anchor="w", padx=15, pady=(0, 15))

    def export_png(self):
        # Hide button before taking screenshot
        self.export_btn.pack_forget()
        self.update()
        
        # Bring window to front to ensure clean screenshot
        self.attributes("-topmost", True)
        self.update()

        try:
            x = self.winfo_rootx()
            y = self.winfo_rooty()
            w = self.winfo_width()
            h = self.winfo_height()
            
            img = ImageGrab.grab(bbox=(x, y, x+w, y+h))
            
            desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
            save_path = os.path.join(desktop, "JamDeck_Kilavuz.png")
            img.save(save_path)
            
            tkinter.messagebox.showinfo("Başarılı", f"Kılavuz harika bir bilgi kartı olarak kaydedildi!\n\nMasaüstü: {save_path}")
        except Exception as e:
            tkinter.messagebox.showerror("Hata", f"PNG kaydedilirken hata oluştu:\n{str(e)}")
        finally:
            self.attributes("-topmost", False)
            self.export_btn.pack(pady=(0, 20), padx=20, fill="x")

if __name__ == "__main__":
    app = GuideApp()
    app.mainloop()
