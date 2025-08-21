import pcbnew
import wx
import wx.grid
import wx.lib.agw.aui as aui
import wx.adv
import csv

# Liste des couches supportées (jusqu'à 20)
layers_list = [1, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20]

def get_dynamic_impact(area_cm2, layers):
    area_m2 = area_cm2 / 10_000.0
    return (7.81 * layers + 57.97) * area_m2

class ModernCarbonImpactFrame(wx.Frame):
    def __init__(self, area_cm2, layers, current_impact):
        super().__init__(None, title="PCB Environmental Impact", size=(1300, 850))
        
        self.area_cm2 = area_cm2
        self.layers = layers
        self.current_impact = current_impact

        self.soft_blue = wx.Colour(74, 144, 226)
        self.green_alt = wx.Colour(120, 200, 120)
        self.red_worse = wx.Colour(220, 100, 100)
        self.current_highlight = wx.Colour(255, 215, 0)
        self.bg_color = wx.Colour(245, 245, 245)
        self.black = wx.Colour(0, 0, 0)

        self._mgr = aui.AuiManager(self)
        panel = wx.Panel(self)
        panel.SetBackgroundColour(self.bg_color)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Bandeau supérieur
        header = wx.Panel(panel)
        header.SetBackgroundColour(self.soft_blue)
        hbox_header = wx.BoxSizer(wx.HORIZONTAL)
        title = wx.StaticText(header, label="🌱 PCB Carbon Footprint Analysis")
        title.SetFont(wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        title.SetForegroundColour(wx.WHITE)
        hbox_header.AddStretchSpacer()
        hbox_header.Add(title, 0, wx.ALL | wx.ALIGN_CENTER, 15)
        hbox_header.AddStretchSpacer()
        header.SetSizer(hbox_header)
        vbox.Add(header, 0, wx.EXPAND)

        # Infos principales (sans encadré, en gros texte)
        infos = wx.BoxSizer(wx.HORIZONTAL)

        def make_info(text, value, color):
            box = wx.BoxSizer(wx.VERTICAL)
            lbl1 = wx.StaticText(panel, label=text)
            lbl1.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            lbl2 = wx.StaticText(panel, label=value)
            lbl2.SetFont(wx.Font(18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            lbl2.SetForegroundColour(color)
            box.Add(lbl1, 0, wx.ALL | wx.ALIGN_CENTER, 5)
            box.Add(lbl2, 0, wx.ALL | wx.ALIGN_CENTER, 5)
            return box

        infos.AddStretchSpacer()
        infos.Add(make_info("Surface Area", f"{area_cm2:.1f} cm²", self.soft_blue), 0, wx.ALL, 15)
        infos.Add(make_info("Layers", f"{layers}", self.soft_blue), 0, wx.ALL, 15)
        infos.Add(make_info("Impact Carbon Footprint", f"{current_impact:.2f} kg CO₂e", self.soft_blue), 0, wx.ALL, 15)
        infos.AddStretchSpacer()
        vbox.Add(infos, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 10)

        # Grille principale
        hbox_grid = wx.BoxSizer(wx.HORIZONTAL)
        self.grid = wx.grid.Grid(panel)
        self.grid.CreateGrid(5, len(layers_list) + 2)  # +2 : Δ% + Surface

        self.grid.EnableEditing(True)
        self.grid.SetRowLabelSize(0)

        # Noms des colonnes
        self.grid.SetColLabelValue(0, "Δ Surface %")
        self.grid.SetColLabelValue(1, "Surface (cm²)")
        for j, layer in enumerate(layers_list, start=2):
            self.grid.SetColLabelValue(j, f"{layer} layer{'s' if layer > 1 else ''}")
            
        self.grid.AutoSizeColumns()

        # Valeurs de la 1ère colonne
        for i, val in enumerate([-20, -10, 0, 10, 20]):
            if val == 0:
                self.grid.SetCellValue(i, 0, "Base")
                self.grid.SetReadOnly(i, 0)
            else:
                self.grid.SetCellValue(i, 0, str(val))
            self.grid.SetCellAlignment(i, 0, wx.ALIGN_CENTER, wx.ALIGN_CENTER)

        self.grid.SetDefaultCellFont(wx.Font(13, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.grid.SetDefaultRowSize(45, True)

        # Largeur colonnes plus grandes
        self.grid.SetColMinimalWidth(0, 200)   # encore plus large
        self.grid.SetColMinimalWidth(1, 200)   # encore plus large

        for j in range(2, self.grid.GetNumberCols()):
            self.grid.SetColMinimalWidth(j, 120)
            for i in range(self.grid.GetNumberRows()):
                self.grid.SetCellAlignment(i, j, wx.ALIGN_CENTER, wx.ALIGN_CENTER)

        self.grid.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.refresh_grid)
        self.grid.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.on_cell_select)

        hbox_grid.AddStretchSpacer(1)
        hbox_grid.Add(self.grid, 0, wx.ALL, 15)
        hbox_grid.AddStretchSpacer(1)
        vbox.Add(hbox_grid, 1, wx.EXPAND)

        # Label unité centré sous le tableau
        unit_lbl = wx.StaticText(panel, label="unit: kgCO\u2082eq")
        font_italic = wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL)
        unit_lbl.SetFont(font_italic)
        hbox_unit = wx.BoxSizer(wx.HORIZONTAL)
        hbox_unit.AddStretchSpacer()
        hbox_unit.Add(unit_lbl, 0, wx.TOP | wx.BOTTOM, 2)  # rapproché
        hbox_unit.AddStretchSpacer()
        vbox.Add(hbox_unit, 0, wx.EXPAND | wx.BOTTOM, 5)

        # Carte détails
        self.detail_panel = wx.Panel(panel)
        self.detail_panel.SetBackgroundColour(wx.WHITE)
        self.detail_panel.SetWindowStyle(wx.BORDER_SIMPLE)
        s_detail = wx.BoxSizer(wx.VERTICAL)
        self.detail_label = wx.StaticText(self.detail_panel, label="Click a cell to see details.")
        self.detail_label.SetFont(wx.Font(13, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        s_detail.Add(self.detail_label, 0, wx.ALL, 12)
        self.detail_panel.SetSizer(s_detail)
        vbox.Add(self.detail_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 20)

        # Footer bar avec boutons
        footer = wx.Panel(panel)
        hbox_footer = wx.BoxSizer(wx.HORIZONTAL)
        btn_export = wx.Button(footer, label="📄 Export CSV", size=(150, 45))
        btn_about = wx.Button(footer, label="ℹ️ About", size=(150, 45))
        btn_close = wx.Button(footer, label="❌ Close", size=(150, 45))
        btn_export.Bind(wx.EVT_BUTTON, self.export_csv)
        btn_about.Bind(wx.EVT_BUTTON, self.show_about)
        btn_close.Bind(wx.EVT_BUTTON, lambda e: self.Close())
        hbox_footer.AddStretchSpacer()
        hbox_footer.Add(btn_export, 0, wx.ALL, 10)
        hbox_footer.Add(btn_about, 0, wx.ALL, 10)
        hbox_footer.Add(btn_close, 0, wx.ALL, 10)
        hbox_footer.AddStretchSpacer()
        footer.SetSizer(hbox_footer)
        vbox.Add(footer, 0, wx.EXPAND | wx.BOTTOM, 10)

        panel.SetSizer(vbox)
        self._mgr.AddPane(panel, aui.AuiPaneInfo().CenterPane().CaptionVisible(False))
        self._mgr.Update()
        self.Centre()
        self.refresh_grid(None)

    def refresh_grid(self, event):
        for i in range(self.grid.GetNumberRows()):
            cell_value = self.grid.GetCellValue(i, 0)
            pct = 0.0 if cell_value == "Base" else float(cell_value)
            area = self.area_cm2 * (1 + pct / 100.0)
            # Colonne Surface
            self.grid.SetCellValue(i, 1, f"{area:.1f}")
            self.grid.SetCellAlignment(i, 1, wx.ALIGN_CENTER, wx.ALIGN_CENTER)

            for j, layer in enumerate(layers_list, start=2):
                val = get_dynamic_impact(area, layer)
                self.grid.SetCellValue(i, j, f"{val:.2f}")
                if abs(area - self.area_cm2) < 0.01 and layer == self.layers:
                    self.grid.SetCellBackgroundColour(i, j, self.current_highlight)
                    self.grid.SetCellTextColour(i, j, wx.BLACK)
                elif val < self.current_impact:
                    self.grid.SetCellBackgroundColour(i, j, self.green_alt)
                    self.grid.SetCellTextColour(i, j, wx.BLACK)
                else:
                    self.grid.SetCellBackgroundColour(i, j, self.red_worse)
                    self.grid.SetCellTextColour(i, j, wx.WHITE)
        self.grid.ForceRefresh()

    def on_cell_select(self, event):
        row, col = event.GetRow(), event.GetCol()
        if col < 2:
            event.Skip()
            return
        val_str = self.grid.GetCellValue(row, col)
        if not val_str:
            return
        val = float(val_str)
        cell_value = self.grid.GetCellValue(row, 0)
        pct = 0.0 if cell_value == "Base" else float(cell_value)
        area = self.area_cm2 * (1 + pct / 100.0)
        diff = val - self.current_impact
        diff_layers = layers_list[col - 2] - self.layers
        detail_text = (
            f"📊 Comparison Details\n"
            f"──────────────────────────────\n"
            f"Surface : {area:.1f} cm² ({pct:+.0f}%)\n"
            f"Layers  : {layers_list[col - 2]} ({diff_layers:+d} vs ref)\n"
            f"Impact  : {val:.2f} kg CO₂e\n"
            f"Δ Impact: {diff:+.2f} kg CO₂e"
        )
        self.detail_label.SetLabel(detail_text)
        event.Skip()

    def export_csv(self, event):
        with wx.FileDialog(self, "Save CSV", wildcard="CSV files (*.csv)|*.csv",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as dlg:
            if dlg.ShowModal() == wx.ID_CANCEL:
                return
            path = dlg.GetPath()
            with open(path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([self.grid.GetColLabelValue(c) for c in range(self.grid.GetNumberCols())])
                for i in range(self.grid.GetNumberRows()):
                    writer.writerow([self.grid.GetCellValue(i, c) for c in range(self.grid.GetNumberCols())])
            wx.MessageBox("CSV exported successfully!", "Export", wx.OK | wx.ICON_INFORMATION)

    def show_about(self, event):
        dlg = wx.Dialog(self, title="About", size=(500, 300))
        vbox = wx.BoxSizer(wx.VERTICAL)

        text1 = wx.StaticText(dlg, label="PCB Carbon Footprint Tool")
        text1.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        vbox.Add(text1, 0, wx.ALL | wx.ALIGN_CENTER, 10)

        # Bloc avec les infos au-dessus
        details_text = (
            "Developed by Alyzée Corre\n"
            "Supervised by Pierre Le Gargasson\n"
            "Company: INSA Rennes, France"
        )
        lbl_details = wx.StaticText(dlg, label=details_text)
        vbox.Add(lbl_details, 0, wx.ALL | wx.ALIGN_LEFT, 10)

        # Ligne avec "Source:" + lien à côté
        hbox_source = wx.BoxSizer(wx.HORIZONTAL)
        lbl_source = wx.StaticText(dlg, label="Source: ")
        link = wx.adv.HyperlinkCtrl(dlg, id=wx.ID_ANY,
            label="PCBnCO Article",
            url="https://hal.science/hal-05054490v1/document")

        hbox_source.Add(lbl_source, 0, wx.ALIGN_CENTER_VERTICAL)
        hbox_source.Add(link, 0, wx.ALIGN_CENTER_VERTICAL)

        vbox.Add(hbox_source, 0, wx.ALL | wx.ALIGN_LEFT, 10)

        # Bouton close
        btn = wx.Button(dlg, wx.ID_OK, "Close")
        vbox.Add(btn, 0, wx.ALL | wx.ALIGN_CENTER, 10)

        dlg.SetSizer(vbox)
        dlg.ShowModal()
        dlg.Destroy()



class CarbonImpactPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "version 14"
        self.category = "Environment"
        self.description = "Estimates the carbon impact of a PCB with a modern UI"
        self.show_toolbar_button = True
        self.icon_file_name = ""

    def Run(self):
        board = pcbnew.GetBoard()
        bbox = board.GetBoardEdgesBoundingBox()
        width_mm = bbox.GetWidth() / 1e6
        height_mm = bbox.GetHeight() / 1e6
        area_cm2 = (width_mm * height_mm) / 100
        copper_layers = board.GetCopperLayerCount()
        current_impact = get_dynamic_impact(area_cm2, copper_layers)
        ModernCarbonImpactFrame(area_cm2, copper_layers, current_impact).Show()

CarbonImpactPlugin().register()

