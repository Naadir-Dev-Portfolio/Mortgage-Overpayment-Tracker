#!/usr/bin/env python3
import sys, json, os, csv
from pathlib import Path
from math import log
from datetime import date
from dateutil.relativedelta import relativedelta
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QDoubleSpinBox, QSpinBox, QDateEdit,
    QPushButton, QFrame, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QSizePolicy,
    QMessageBox, QCheckBox, QAbstractSpinBox
)
from PyQt6.QtCore import Qt, QDate, QTimer, QSize, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPixmap
import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.ticker as mticker
import numpy as np

# ─────────────────────────────────────────────
#  COLOUR PALETTE  (Document OCR Studio-inspired charcoal theme)
# ─────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent
LOGO_PATH = ROOT_DIR / "images" / "logo.png"

BG_DARK  = "#070909"
CARD_BG  = "#0d1113"
PANEL_BG = "#0a0d0f"
INPUT_BG = "#050708"
BORDER   = "#232b2f"
TEXT     = "#f0f5f3"
TEXT_DIM = "#94a19d"

ACCENT   = "#1fa99a"
ACCENT2  = "#b8842a"
GREEN    = "#6fc38d"
YELLOW   = "#c58f2f"
DANGER   = "#e05f57"

CHART_COLORS = [ACCENT, GREEN, ACCENT2, "#5d8bb8", "#9b6cb7", DANGER, "#8fa260"]

# ─────────────────────────────────────────────
#  SMART SPINBOX  — select-all on focus / click
# ─────────────────────────────────────────────
class SmartSpin(QDoubleSpinBox):
    """Double spinbox that selects all text when focused or clicked,
    so typing immediately overwrites the current value."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setGroupSeparatorShown(True)
        self.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        QTimer.singleShot(0, self.selectAll)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        QTimer.singleShot(0, self.selectAll)


class SmartIntSpin(QSpinBox):
    """Integer spinbox with the same select-all behaviour."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        QTimer.singleShot(0, self.selectAll)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        QTimer.singleShot(0, self.selectAll)

# ─────────────────────────────────────────────
#  STYLESHEET
# ─────────────────────────────────────────────
def stylesheet() -> str:
    return f"""
    QMainWindow, QWidget {{
        background: {BG_DARK};
        color: {TEXT};
        font-family: 'Segoe UI';
        font-size: 13px;
    }}
    QFrame#card {{
        background: {CARD_BG};
        border: 1px solid {BORDER};
        border-radius: 10px;
    }}
    QFrame#sidebar {{
        background: {PANEL_BG};
        border-right: 1px solid {BORDER};
    }}
    QFrame#topBar {{
        background: {PANEL_BG};
        border-bottom: 1px solid {BORDER};
    }}
    QLabel {{ color: {TEXT}; background: transparent; }}
    QLabel#heading   {{ font-size: 21px; font-weight: 700; color: {TEXT}; }}
    QLabel#subhead   {{ font-size: 12px; font-weight: 700; color: {TEXT_DIM};
                        padding-top: 7px; border-top: 1px solid {BORDER}; }}
    QLabel#dim       {{ color: {TEXT_DIM}; font-size: 12px; }}
    QLabel#kpi       {{ font-size: 24px; font-weight: 700; color: {ACCENT}; }}
    QLabel#kpi2      {{ font-size: 24px; font-weight: 700; color: {GREEN};  }}
    QLabel#kpi3      {{ font-size: 24px; font-weight: 700; color: {YELLOW}; }}
    QLabel#kpi4      {{ font-size: 24px; font-weight: 700; color: {ACCENT2};}}

    QDoubleSpinBox, QSpinBox, QDateEdit, QComboBox {{
        background: {INPUT_BG};
        color: {TEXT};
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 5px 10px;
        font-size: 13px;
        selection-background-color: {ACCENT};
        selection-color: #061312;
    }}
    QDoubleSpinBox::up-button, QSpinBox::up-button,
    QDoubleSpinBox::down-button, QSpinBox::down-button {{
        width: 21px;
        border: none;
        background: {CARD_BG};
        border-radius: 3px;
    }}
    QDoubleSpinBox::up-button:hover, QSpinBox::up-button:hover,
    QDoubleSpinBox::down-button:hover, QSpinBox::down-button:hover {{
        background: {BORDER};
    }}
    QDoubleSpinBox::up-arrow, QSpinBox::up-arrow {{
        image: none; width: 0; height: 0;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-bottom: 6px solid {TEXT_DIM};
    }}
    QDoubleSpinBox::down-arrow, QSpinBox::down-arrow {{
        image: none; width: 0; height: 0;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 6px solid {TEXT_DIM};
    }}
    QDoubleSpinBox:focus, QSpinBox:focus, QDateEdit:focus {{
        border: 1px solid {ACCENT};
        background: {CARD_BG};
    }}

    QPushButton {{
        background: {ACCENT};
        color: #061312;
        border: none;
        border-radius: 7px;
        padding: 8px 18px;
        font-size: 13px;
        font-weight: 600;
    }}
    QPushButton:hover   {{ background: #38caba; }}
    QPushButton:pressed {{ background: #1f8f83; }}
    QPushButton#secondary {{
        background: {CARD_BG};
        color: {TEXT};
        border: 1px solid {BORDER};
    }}
    QPushButton#secondary:hover {{ background: {BORDER}; }}
    QPushButton#green {{
        background: {GREEN};
        color: {BG_DARK};
    }}
    QPushButton#green:hover {{ background: #93dba8; }}

    QTabWidget::pane {{ border: none; background: {BG_DARK}; }}
    QTabWidget::tab-bar {{ left: 0px; }}
    QTabBar::tab {{
        background: {CARD_BG};
        color: {TEXT_DIM};
        border: none;
        padding: 10px 24px;
        font-size: 13px;
        font-weight: 600;
        margin-right: 2px;
        border-radius: 8px 8px 0 0;
    }}
    QTabBar::tab:selected {{ background: {ACCENT}; color: #061312; }}
    QTabBar::tab:hover:!selected {{ background: {BORDER}; color: {TEXT}; }}

    QScrollBar:vertical {{
        background: {PANEL_BG}; width: 5px; margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {BORDER}; border-radius: 2px; min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {ACCENT}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar:horizontal {{
        background: {PANEL_BG}; height: 5px;
    }}
    QScrollBar::handle:horizontal {{
        background: {BORDER}; border-radius: 2px; min-width: 24px;
    }}
    QScrollBar::handle:horizontal:hover {{ background: {ACCENT}; }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

    QTableWidget {{
        background: {CARD_BG};
        color: {TEXT};
        gridline-color: {BORDER};
        border: none;
        border-radius: 8px;
        font-size: 12px;
    }}
    QTableWidget::item {{ padding: 5px 10px; }}
    QTableWidget::item:selected {{ background: {ACCENT}; color: #061312; }}
    QHeaderView::section {{
        background: {PANEL_BG};
        color: {TEXT_DIM};
        border: none;
        padding: 8px 10px;
        font-size: 12px;
        font-weight: 600;
    }}

    QCheckBox {{ color: {TEXT}; spacing: 6px; }}
    QCheckBox::indicator {{
        width: 15px; height: 15px;
        border-radius: 4px;
        border: 1px solid {BORDER};
        background: {INPUT_BG};
    }}
    QCheckBox::indicator:checked {{
        background: {ACCENT};
        border: 1px solid {ACCENT};
    }}

    QGroupBox {{
        color: {TEXT_DIM};
        border: 1px solid {BORDER};
        border-radius: 7px;
        margin-top: 10px;
        padding-top: 10px;
        font-size: 12px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 4px;
    }}
    """

# ─────────────────────────────────────────────
#  MORTGAGE CALCULATION ENGINE
#  Key fix: initial payment is calculated ONCE and held fixed.
#  Overpayments are applied on top of that fixed payment, reducing
#  the principal faster and ending the mortgage early.
# ─────────────────────────────────────────────
class MortgageCalc:
    def __init__(self, principal: float, annual_rate: float, term_months: int,
                 start_date: date, monthly_overpay: float = 0.0,
                 lump_sums: list = None,
                 rate2: float = None, rate2_start_month: int = None):
        self.principal          = principal
        self.annual_rate        = annual_rate
        self.term_months        = term_months
        self.start_date         = start_date
        self.monthly_overpay    = monthly_overpay
        self.lump_sums          = {ls["month"]: ls["amount"] for ls in (lump_sums or [])}
        self.rate2              = rate2
        self.rate2_start_month  = rate2_start_month

    @staticmethod
    def _payment(balance: float, monthly_rate: float, remaining_months: int) -> float:
        if monthly_rate == 0:
            return balance / remaining_months
        r, n = monthly_rate, remaining_months
        return balance * r * (1 + r) ** n / ((1 + r) ** n - 1)

    def simulate(self) -> list[dict]:
        balance = self.principal
        mr1     = self.annual_rate / 12 / 100

        # Fixed initial payment (standard amortisation)
        fixed_pmt = self._payment(balance, mr1, self.term_months)

        schedule  = []
        for m in range(1, self.term_months + 1):
            if balance <= 0:
                break

            # Switch to variable rate: recalculate payment on remaining balance/term
            if (self.rate2 is not None and
                    self.rate2_start_month is not None and
                    m == self.rate2_start_month):
                mr1       = self.rate2 / 12 / 100
                remaining = self.term_months - m + 1
                fixed_pmt = self._payment(balance, mr1, remaining)

            mr       = mr1
            interest = balance * mr

            # How much of the fixed payment goes to principal
            principal_part = max(0.0, fixed_pmt - interest)

            # Overpayment (cannot overpay more than remaining balance)
            extra = self.monthly_overpay + self.lump_sums.get(m, 0.0)
            actual_extra = min(extra, max(0.0, balance - principal_part))

            total_pmt = fixed_pmt + actual_extra
            balance   = max(0.0, balance - principal_part - actual_extra)

            pmt_date  = self.start_date + relativedelta(months=m - 1)
            schedule.append({
                "month":       m,
                "date":        pmt_date,
                "payment":     total_pmt,
                "principal":   principal_part + actual_extra,
                "interest":    interest,
                "balance":     balance,
                "overpayment": actual_extra,
                "fixed_pmt":   fixed_pmt,
            })
            if balance == 0.0:
                break

        return schedule

    def simulate_base(self) -> list[dict]:
        """Simulate without any overpayments (baseline for comparison)."""
        orig_op, orig_ls       = self.monthly_overpay, self.lump_sums
        self.monthly_overpay   = 0.0
        self.lump_sums         = {}
        result = self.simulate()
        self.monthly_overpay   = orig_op
        self.lump_sums         = orig_ls
        return result

    @staticmethod
    def stamp_duty(price: float, is_first_buyer: bool = False,
                   is_additional: bool = False) -> float:
        """UK Stamp Duty Land Tax — rates from April 2025."""
        if is_additional:
            bands = [(250_000, 0.05), (925_000, 0.10),
                     (1_500_000, 0.15), (float("inf"), 0.17)]
        elif is_first_buyer and price <= 625_000:
            bands = [(425_000, 0.00), (625_000, 0.05)]
        else:
            bands = [(250_000, 0.00), (925_000, 0.05),
                     (1_500_000, 0.10), (float("inf"), 0.12)]
        tax, prev = 0.0, 0
        for limit, rate in bands:
            chunk = min(price, limit) - prev
            if chunk <= 0:
                break
            tax  += chunk * rate
            prev  = limit
        return tax

    @staticmethod
    def overpayment_for_target(principal, annual_rate, term_months, start_date,
                                target_months: int,
                                rate2=None, rate2_start=None) -> float:
        """Binary search: monthly overpayment needed to pay off in target_months."""
        lo, hi = 0.0, principal
        for _ in range(60):
            mid  = (lo + hi) / 2
            calc = MortgageCalc(principal, annual_rate, term_months, start_date, mid,
                                rate2=rate2, rate2_start_month=rate2_start)
            if len(calc.simulate()) <= target_months:
                hi = mid
            else:
                lo = mid
        return round((lo + hi) / 2, 2)

# ─────────────────────────────────────────────
#  CHART CANVAS WRAPPER
# ─────────────────────────────────────────────
class ChartCanvas(FigureCanvas):
    def __init__(self, parent=None, figsize=(8, 3.8)):
        self.fig, self.ax = Figure(figsize=figsize, facecolor=CARD_BG), None
        self.ax = self.fig.add_subplot(111, facecolor=CARD_BG)
        super().__init__(self.fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._style()

    def _style(self):
        self.ax.tick_params(colors=TEXT_DIM, labelsize=10)
        for sp in self.ax.spines.values():
            sp.set_color(BORDER)
        self.ax.xaxis.label.set_color(TEXT_DIM)
        self.ax.yaxis.label.set_color(TEXT_DIM)
        self.fig.tight_layout(pad=1.6)

    def clear(self):
        self.ax.cla()
        self.ax.set_facecolor(CARD_BG)
        self._style()

    def fmt_currency(self):
        self.ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda v, _: f"£{v:,.0f}"))


class DualChartCanvas(FigureCanvas):
    """Two side-by-side axes."""
    def __init__(self, parent=None, figsize=(12, 3.8)):
        self.fig = Figure(figsize=figsize, facecolor=CARD_BG)
        self.ax1 = self.fig.add_subplot(121, facecolor=CARD_BG)
        self.ax2 = self.fig.add_subplot(122, facecolor=CARD_BG)
        super().__init__(self.fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._style()

    def _style(self):
        for ax in (self.ax1, self.ax2):
            ax.tick_params(colors=TEXT_DIM, labelsize=10)
            for sp in ax.spines.values():
                sp.set_color(BORDER)
        self.fig.tight_layout(pad=1.6)

    def clear(self):
        for ax in (self.ax1, self.ax2):
            ax.cla()
            ax.set_facecolor(CARD_BG)
        self._style()

    def fmt_currency(self, ax):
        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda v, _: f"£{v:,.0f}"))

# ─────────────────────────────────────────────
#  METRIC CARD WIDGET
# ─────────────────────────────────────────────
class MetricCard(QFrame):
    def __init__(self, title: str, value: str = "—",
                 sub: str = "", kpi_id: str = "kpi", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setMinimumWidth(130)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(3)
        self._t = QLabel(title);   self._t.setObjectName("dim")
        self._v = QLabel(value);   self._v.setObjectName(kpi_id)
        self._s = QLabel(sub);     self._s.setObjectName("dim"); self._s.setWordWrap(True)
        for w in (self._t, self._v, self._s):
            lay.addWidget(w)

    def update(self, value: str, sub: str = ""):
        self._v.setText(value)
        self._s.setText(sub)

# ─────────────────────────────────────────────
#  SIDEBAR INPUT PANEL
# ─────────────────────────────────────────────
class Sidebar(QFrame):
    calculate_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(318)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        L = QVBoxLayout(self)
        L.setContentsMargins(18, 16, 18, 18)
        L.setSpacing(8)

        # ── title ──
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 6)
        title_row.setSpacing(12)
        if LOGO_PATH.exists():
            logo = QLabel()
            logo.setFixedSize(36, 36)
            logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            logo.setPixmap(
                QPixmap(str(LOGO_PATH)).scaled(
                    QSize(34, 34),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            title_row.addWidget(logo)
        t = QLabel("Mortgage Details")
        t.setObjectName("heading")
        t.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        title_row.addWidget(t)
        title_row.addStretch()
        L.addLayout(title_row)

        # ── Property & loan ──
        L.addWidget(self._sec("Property & Loan"))
        self.price   = self._spin("Property Price",  0, 5_000_000, 350_000, L, "£ ", 0)
        self.deposit = self._spin("Deposit",         0, 5_000_000,  50_000, L, "£ ", 0)
        self.ltv_lbl = QLabel("LTV: —  |  Loan: —")
        self.ltv_lbl.setObjectName("dim")
        L.addWidget(self.ltv_lbl)
        self.price.valueChanged.connect(self._update_ltv)
        self.deposit.valueChanged.connect(self._update_ltv)

        # ── Rate & term ──
        L.addWidget(self._sec("Interest & Term"))
        self.rate     = self._spin("Initial Rate (%)", 0,  20,  4.5, L, "", 2, 0.05)
        self.term_yrs = self._spin("Term (years)",     1,  40,   25, L, "", 0, 1)
        L.addWidget(QLabel("Start Date"))
        self.start_dt = QDateEdit(QDate.currentDate())
        self.start_dt.setCalendarPopup(True)
        self.start_dt.setDisplayFormat("dd/MM/yyyy")
        L.addWidget(self.start_dt)

        # ── Variable rate ──
        self.chk_rate2 = QCheckBox("Variable rate after fixed period")
        L.addWidget(self.chk_rate2)
        self._r2f = QFrame(); r2l = QVBoxLayout(self._r2f)
        r2l.setContentsMargins(0, 0, 0, 0); r2l.setSpacing(6)
        self.fix_yrs  = self._spin("Fixed period (yrs)", 1, 40, 2,   None, "", 0, 1)
        self.rate2    = self._spin("Variable rate (%)",  0, 20, 6.5, None, "", 2, 0.05)
        for lbl, w in [("Fixed period (yrs)", self.fix_yrs), ("Variable rate (%)", self.rate2)]:
            r2l.addWidget(QLabel(lbl)); r2l.addWidget(w)
        self._r2f.setVisible(False)
        L.addWidget(self._r2f)
        self.chk_rate2.toggled.connect(self._r2f.setVisible)

        # ── Overpayments ──
        L.addWidget(self._sec("Overpayments"))
        self.overpay = self._spin("Monthly Overpayment", 0, 50_000, 0, L, "£ ", 0, 50)
        L.addWidget(QLabel("One-off Lump Sum"))
        ls_row = QHBoxLayout()
        self.lump_mo  = SmartIntSpin(); self.lump_mo.setRange(1, 600); self.lump_mo.setPrefix("Mo ")
        self.lump_amt = SmartSpin();    self.lump_amt.setRange(0, 500_000); self.lump_amt.setPrefix("£ ")
        self.lump_amt.setDecimals(0);   self.lump_amt.setSingleStep(1000); self.lump_amt.setGroupSeparatorShown(True)
        ls_row.setSpacing(8)
        self.lump_mo.setMinimumWidth(96)
        self.lump_amt.setMinimumWidth(118)
        ls_row.addWidget(self.lump_mo, 1); ls_row.addWidget(self.lump_amt, 1)
        L.addLayout(ls_row)
        b_add = QPushButton("+ Add Lump Sum"); b_add.setObjectName("secondary")
        b_add.clicked.connect(self._add_lump); L.addWidget(b_add)
        self._lumps: list[dict] = []
        self._lump_lay = QVBoxLayout(); L.addLayout(self._lump_lay)

        # ── Stamp Duty ──
        L.addWidget(self._sec("Stamp Duty (SDLT)"))
        self.chk_sd = QCheckBox("Show stamp duty estimate"); L.addWidget(self.chk_sd)
        self._sdf = QFrame(); sdl = QVBoxLayout(self._sdf)
        sdl.setContentsMargins(0, 0, 0, 0); sdl.setSpacing(5)
        self.chk_ftb  = QCheckBox("First-time buyer")
        self.chk_add  = QCheckBox("Additional property (+3%)")
        self.sd_lbl   = QLabel("SDLT: —"); self.sd_lbl.setObjectName("dim")
        for w in (self.chk_ftb, self.chk_add, self.sd_lbl):
            sdl.addWidget(w)
        self._sdf.setVisible(False); L.addWidget(self._sdf)
        self.chk_sd.toggled.connect(self._sdf.setVisible)
        self.price.valueChanged.connect(self._update_sd)
        self.chk_ftb.toggled.connect(self._update_sd)
        self.chk_add.toggled.connect(self._update_sd)

        # ── Save / Load ──
        L.addWidget(self._sec("Session"))
        sl = QHBoxLayout()
        sl.setSpacing(8)
        bs = QPushButton("Save"); bs.setObjectName("secondary"); bs.clicked.connect(self._save)
        bl = QPushButton("Load"); bl.setObjectName("secondary"); bl.clicked.connect(self._load)
        sl.addWidget(bs, 1); sl.addWidget(bl, 1); L.addLayout(sl)

        # ── Calculate ──
        L.addSpacing(4)
        self.b_calc = QPushButton("Calculate  ▶")
        self.b_calc.setObjectName("green")
        self.b_calc.setMinimumHeight(42)
        self.b_calc.clicked.connect(self.calculate_requested.emit)
        L.addWidget(self.b_calc)
        L.addStretch()

        self._update_ltv()
        self._load_initial()

    # ── helpers ──────────────────────────────
    def _sec(self, txt: str) -> QLabel:
        l = QLabel(txt); l.setObjectName("subhead")
        l.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        return l

    def _spin(self, label, lo, hi, default, layout, prefix="", dec=2, step=None) -> SmartSpin:
        w = SmartSpin()
        w.setDecimals(dec); w.setRange(lo, hi); w.setValue(default)
        if prefix: w.setPrefix(prefix)
        if step:   w.setSingleStep(step)
        if layout:
            layout.addWidget(QLabel(label)); layout.addWidget(w)
        return w

    def _update_ltv(self):
        loan = max(0, self.price.value() - self.deposit.value())
        ltv  = loan / self.price.value() * 100 if self.price.value() else 0
        self.ltv_lbl.setText(f"LTV: {ltv:.1f}%  |  Loan: £{loan:,.0f}")

    def _update_sd(self):
        if not self.chk_sd.isChecked(): return
        tax = MortgageCalc.stamp_duty(self.price.value(),
                                       self.chk_ftb.isChecked(),
                                       self.chk_add.isChecked())
        self.sd_lbl.setText(f"SDLT: £{tax:,.0f}")

    def _add_lump(self):
        a = self.lump_amt.value()
        if a <= 0: return
        m = self.lump_mo.value()
        self._lumps.append({"month": m, "amount": a})
        lbl = QLabel(f"  Month {m}: £{a:,.0f}"); lbl.setObjectName("dim")
        self._lump_lay.addWidget(lbl)

    def get_params(self) -> dict:
        loan = max(0, self.price.value() - self.deposit.value())
        sd   = self.start_dt.date()
        r2   = self.rate2.value() if self.chk_rate2.isChecked() else None
        r2m  = int(self.fix_yrs.value() * 12) if self.chk_rate2.isChecked() else None
        return dict(
            principal       = loan,
            annual_rate     = self.rate.value(),
            term_months     = int(self.term_yrs.value() * 12),
            start_date      = date(sd.year(), sd.month(), sd.day()),
            monthly_overpay = self.overpay.value(),
            lump_sums       = list(self._lumps),
            rate2           = r2,
            rate2_start_month = r2m,
            price           = self.price.value(),
            deposit         = self.deposit.value(),
        )

    def _save(self):
        p = QFileDialog.getSaveFileName(self, "Save Session", "", "JSON (*.json)")[0]
        if not p: return
        d = self.get_params(); d["start_date"] = d["start_date"].isoformat()
        with open(p, "w") as f: json.dump(d, f, indent=2)

    def _load(self):
        p = QFileDialog.getOpenFileName(self, "Load Session", "", "JSON (*.json)")[0]
        if not p: return
        with open(p) as f: d = json.load(f)
        self.price.setValue(d.get("price", 350_000))
        self.deposit.setValue(d.get("deposit", 50_000))
        self.rate.setValue(d.get("annual_rate", 4.5))
        self.term_yrs.setValue(d.get("term_months", 300) / 12)
        self.overpay.setValue(d.get("monthly_overpay", 0))
        if "start_date" in d:
            dt = date.fromisoformat(d["start_date"])
            self.start_dt.setDate(QDate(dt.year, dt.month, dt.day))

    def _load_initial(self):
        p = os.path.join(os.path.dirname(__file__), "initial.json")
        if not os.path.exists(p): return
        try:
            with open(p) as f: d = json.load(f)
            self.price.setValue(d.get("price", d.get("property_price", 350_000)))
            dep  = d.get("deposit", 0)
            loan = d.get("principal", d.get("loan_amount", 0))
            if dep:
                self.deposit.setValue(dep)
            elif loan:
                self.deposit.setValue(max(0, self.price.value() - loan))
            self.rate.setValue(d.get("annual_rate", d.get("interest_rate", 4.5)))
            self.term_yrs.setValue(d.get("term_months", d.get("term_years", 25) * 12) / 12)
            self.overpay.setValue(d.get("monthly_overpay", d.get("overpayment", 0)))
        except Exception:
            pass

# ─────────────────────────────────────────────
#  CHART DRAWING FUNCTIONS
# ─────────────────────────────────────────────
def draw_balance(canvas: ChartCanvas, base: list, op: list):
    canvas.clear()
    ax = canvas.ax
    db = [r["date"] for r in base]; bb = [r["balance"] for r in base]
    do = [r["date"] for r in op];   bo = [r["balance"] for r in op]
    ax.fill_between(db, bb, alpha=0.08, color=TEXT_DIM)
    ax.plot(db, bb, color=TEXT_DIM, lw=1.5, ls="--", label="No overpayment")
    ax.fill_between(do, bo, alpha=0.15, color=ACCENT)
    ax.plot(do, bo, color=ACCENT, lw=2.2, label="With overpayment")
    if len(do) < len(db):
        ax.axvline(do[-1], color=GREEN, lw=1.2, ls=":", alpha=0.8)
        ax.annotate("Early payoff", xy=(do[-1], 0), xytext=(12, 32),
                    textcoords="offset points", color=GREEN, fontsize=9,
                    arrowprops=dict(arrowstyle="->", color=GREEN, lw=0.8))
    ax.set_title("Outstanding Balance Over Time", color=TEXT, fontsize=12, pad=8)
    ax.legend(facecolor=PANEL_BG, labelcolor=TEXT, framealpha=0.9, fontsize=10, edgecolor=BORDER)
    canvas.fmt_currency(); canvas.fig.tight_layout(pad=1.6); canvas.draw()


def draw_equity(canvas: ChartCanvas, price: float, base: list, op: list):
    canvas.clear(); ax = canvas.ax
    db = [r["date"] for r in base]; eb = [price - r["balance"] for r in base]
    do = [r["date"] for r in op];   eo = [price - r["balance"] for r in op]
    ax.fill_between(db, eb, alpha=0.08, color=YELLOW)
    ax.plot(db, eb, color=YELLOW, lw=1.5, ls="--", label="Equity (base)")
    ax.fill_between(do, eo, alpha=0.15, color=GREEN)
    ax.plot(do, eo, color=GREEN, lw=2.2, label="Equity (w/ overpay)")
    ax.axhline(price, color=ACCENT2, lw=1, ls=":", alpha=0.5)
    ax.set_title("Equity Built Over Time", color=TEXT, fontsize=12, pad=8)
    ax.legend(facecolor=PANEL_BG, labelcolor=TEXT, framealpha=0.9, fontsize=10, edgecolor=BORDER)
    canvas.fmt_currency(); canvas.fig.tight_layout(pad=1.6); canvas.draw()


def draw_composition(canvas: ChartCanvas, op: list):
    canvas.clear(); ax = canvas.ax
    dates = [r["date"] for r in op]
    intr  = [r["interest"]    for r in op]
    prin  = [r["principal"]   for r in op]
    xtra  = [r["overpayment"] for r in op]
    ax.stackplot(dates, intr, prin, xtra,
                 labels=["Interest", "Principal", "Overpayment"],
                 colors=[ACCENT2, ACCENT, GREEN], alpha=0.88)
    ax.set_title("Monthly Payment Composition", color=TEXT, fontsize=12, pad=8)
    ax.legend(facecolor=PANEL_BG, labelcolor=TEXT, framealpha=0.9, fontsize=10,
              edgecolor=BORDER, loc="upper right")
    canvas.fmt_currency(); canvas.fig.tight_layout(pad=1.6); canvas.draw()


def draw_annual(canvas: DualChartCanvas, base: list, op: list):
    canvas.clear()
    def ann(sched):
        y: dict = {}
        for r in sched:
            yr = r["date"].year
            if yr not in y: y[yr] = {"i": 0, "p": 0}
            y[yr]["i"] += r["interest"]
            y[yr]["p"] += r["principal"]
        return y
    yb, yo = ann(base), ann(op)
    years  = sorted(set(yb) | set(yo))
    x = np.arange(len(years)); w = 0.38

    # left: interest comparison
    ax1 = canvas.ax1
    ax1.bar(x - w/2, [yb.get(y, {}).get("i", 0) for y in years], w, color=TEXT_DIM, alpha=0.65, label="Base")
    ax1.bar(x + w/2, [yo.get(y, {}).get("i", 0) for y in years], w, color=ACCENT2, alpha=0.9, label="w/ overpay")
    ax1.set_xticks(x); ax1.set_xticklabels([str(y) for y in years], rotation=50, ha="right", fontsize=8)
    ax1.set_title("Annual Interest Paid", color=TEXT, fontsize=11, pad=6)
    ax1.legend(facecolor=PANEL_BG, labelcolor=TEXT, framealpha=0.9, fontsize=9, edgecolor=BORDER)
    canvas.fmt_currency(ax1)

    # right: cumulative savings
    ax2 = canvas.ax2
    cum_b = np.cumsum([sum(r["interest"] for r in base if r["date"].year <= y) for y in years])
    cum_o = np.cumsum([sum(r["interest"] for r in op   if r["date"].year <= y) for y in years])
    # simpler: cumulative over schedule
    cb = np.cumsum([r["interest"] for r in base])
    co_dates = [r["date"] for r in op]
    cb_dates = [r["date"] for r in base]
    ax2.plot(cb_dates, cb, color=TEXT_DIM, lw=1.5, ls="--", label="Cumulative interest (base)")
    ax2.plot(co_dates, np.cumsum([r["interest"] for r in op]),
             color=GREEN, lw=2.2, label="Cumulative interest (w/ overpay)")
    ax2.set_title("Cumulative Interest", color=TEXT, fontsize=11, pad=6)
    ax2.legend(facecolor=PANEL_BG, labelcolor=TEXT, framealpha=0.9, fontsize=9, edgecolor=BORDER)
    canvas.fmt_currency(ax2)
    canvas.fig.tight_layout(pad=1.6); canvas.draw()


def draw_savings(canvas: ChartCanvas, base: list, op: list):
    canvas.clear(); ax = canvas.ax
    db = [r["date"] for r in base]; cb = np.cumsum([r["payment"] for r in base])
    do = [r["date"] for r in op];   co = np.cumsum([r["payment"] for r in op])
    ax.plot(db, cb, color=TEXT_DIM, lw=1.5, ls="--", label="Total paid (base)")
    ax.plot(do, co, color=GREEN,    lw=2.2, label="Total paid (w/ overpay)")
    n = min(len(base), len(op))
    savings = [cb[i] - co[i] for i in range(n)]
    ax.fill_between(do[:n], savings, alpha=0.12, color=GREEN)
    ax.set_title("Cumulative Total Cost vs Savings", color=TEXT, fontsize=12, pad=8)
    ax.legend(facecolor=PANEL_BG, labelcolor=TEXT, framealpha=0.9, fontsize=10, edgecolor=BORDER)
    canvas.fmt_currency(); canvas.fig.tight_layout(pad=1.6); canvas.draw()


def draw_scenarios(canvas: ChartCanvas, scenarios: list[tuple[str, list]]):
    canvas.clear(); ax = canvas.ax
    for i, (label, sched) in enumerate(scenarios):
        ax.plot([r["date"] for r in sched], [r["balance"] for r in sched],
                color=CHART_COLORS[i % len(CHART_COLORS)], lw=2.0, label=label)
    ax.set_title("Overpayment Scenarios — Balance", color=TEXT, fontsize=12, pad=8)
    ax.legend(facecolor=PANEL_BG, labelcolor=TEXT, framealpha=0.9, fontsize=10, edgecolor=BORDER)
    canvas.fmt_currency(); canvas.fig.tight_layout(pad=1.6); canvas.draw()

# ─────────────────────────────────────────────
#  DASHBOARD TAB
# ─────────────────────────────────────────────
class DashboardTab(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14); root.setSpacing(12)

        kpi_row = QHBoxLayout(); kpi_row.setSpacing(10)
        self.kpi_pmt    = MetricCard("Monthly Payment",  kpi_id="kpi")
        self.kpi_total  = MetricCard("Total Cost",       kpi_id="kpi2")
        self.kpi_intr   = MetricCard("Total Interest",   kpi_id="kpi3")
        self.kpi_save   = MetricCard("Interest Saved",   kpi_id="kpi4")
        self.kpi_payoff = MetricCard("Payoff Date",      kpi_id="kpi")
        self.kpi_months = MetricCard("Months Saved",     kpi_id="kpi2")
        for k in (self.kpi_pmt, self.kpi_total, self.kpi_intr,
                  self.kpi_save, self.kpi_payoff, self.kpi_months):
            kpi_row.addWidget(k)
        root.addLayout(kpi_row)

        for canvas_attr, figsize in [("bal_canvas", (10, 3.8)), ("eq_canvas", (10, 3.0))]:
            card = QFrame(); card.setObjectName("card")
            cl   = QVBoxLayout(card); cl.setContentsMargins(10, 10, 10, 10)
            c    = ChartCanvas(figsize=figsize); setattr(self, canvas_attr, c)
            cl.addWidget(c); root.addWidget(card, stretch=1)

    def refresh(self, params, base, op):
        pmt    = op[0]["fixed_pmt"] if op else 0
        total  = sum(r["payment"]  for r in op)
        intr   = sum(r["interest"] for r in op)
        b_intr = sum(r["interest"] for r in base)
        saving = max(0, b_intr - intr)
        months = max(0, len(base) - len(op))
        payoff = op[-1]["date"].strftime("%b %Y") if op else "—"
        self.kpi_pmt.update(f"£{pmt:,.0f}")
        self.kpi_total.update(f"£{total:,.0f}")
        self.kpi_intr.update(f"£{intr:,.0f}")
        self.kpi_save.update(f"£{saving:,.0f}")
        self.kpi_payoff.update(payoff)
        self.kpi_months.update(f"{months} months",
                                f"({months//12}y {months%12}m)" if months else "On original schedule")
        draw_balance(self.bal_canvas, base, op)
        draw_equity(self.eq_canvas,  params["price"], base, op)

# ─────────────────────────────────────────────
#  ANALYSIS TAB
# ─────────────────────────────────────────────
class AnalysisTab(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14); root.setSpacing(12)

        # Composition chart (full width)
        c1 = QFrame(); c1.setObjectName("card")
        l1 = QVBoxLayout(c1); l1.setContentsMargins(10, 10, 10, 10)
        self.comp_canvas = ChartCanvas(figsize=(10, 3.4))
        l1.addWidget(self.comp_canvas)
        root.addWidget(c1, stretch=1)

        # Annual & cumulative (dual)
        c2 = QFrame(); c2.setObjectName("card")
        l2 = QVBoxLayout(c2); l2.setContentsMargins(10, 10, 10, 10)
        self.ann_canvas = DualChartCanvas(figsize=(12, 3.4))
        l2.addWidget(self.ann_canvas)
        root.addWidget(c2, stretch=1)

        # Savings
        c3 = QFrame(); c3.setObjectName("card")
        l3 = QVBoxLayout(c3); l3.setContentsMargins(10, 10, 10, 10)
        self.sav_canvas = ChartCanvas(figsize=(10, 3.0))
        l3.addWidget(self.sav_canvas)
        root.addWidget(c3, stretch=1)

    def refresh(self, base, op):
        draw_composition(self.comp_canvas, op)
        draw_annual(self.ann_canvas, base, op)
        draw_savings(self.sav_canvas, base, op)

# ─────────────────────────────────────────────
#  SCENARIOS TAB
# ─────────────────────────────────────────────
class ScenariosTab(QWidget):
    def __init__(self):
        super().__init__()
        self._params = None
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14); root.setSpacing(12)

        # Controls
        ctl = QFrame(); ctl.setObjectName("card")
        cl  = QHBoxLayout(ctl); cl.setContentsMargins(14, 10, 14, 10); cl.setSpacing(16)
        self._spins: list[SmartSpin] = []
        defaults = [0, 200, 500, 1000]
        for i in range(4):
            col = QVBoxLayout()
            col.addWidget(QLabel(f"Scenario {i+1}  (£/mo)"))
            sp = SmartSpin(); sp.setRange(0, 50_000); sp.setDecimals(0)
            sp.setPrefix("£ "); sp.setSingleStep(50); sp.setValue(defaults[i])
            sp.setGroupSeparatorShown(True)
            col.addWidget(sp); cl.addLayout(col); self._spins.append(sp)
        b_run = QPushButton("Run Scenarios"); b_run.setMinimumHeight(38)
        b_run.clicked.connect(self._run); cl.addWidget(b_run)
        root.addWidget(ctl)

        # Chart
        cc = QFrame(); cc.setObjectName("card")
        ccl = QVBoxLayout(cc); ccl.setContentsMargins(10, 10, 10, 10)
        self.sc_canvas = ChartCanvas(figsize=(10, 4.2))
        ccl.addWidget(self.sc_canvas)
        root.addWidget(cc, stretch=1)

        # Summary cards
        sr = QHBoxLayout(); sr.setSpacing(10)
        self._scards: list[MetricCard] = []
        ids = ["kpi", "kpi2", "kpi3", "kpi4"]
        for i in range(4):
            mc = MetricCard(f"Scenario {i+1}", "—", kpi_id=ids[i])
            sr.addWidget(mc); self._scards.append(mc)
        root.addLayout(sr)

        # Target calculator
        tgt = QFrame(); tgt.setObjectName("card")
        tl  = QHBoxLayout(tgt); tl.setContentsMargins(14, 10, 14, 10); tl.setSpacing(14)
        tl.addWidget(QLabel("Pay off in (years):"))
        self.tgt_y = SmartIntSpin(); self.tgt_y.setRange(1, 40); self.tgt_y.setValue(15)
        tl.addWidget(self.tgt_y)
        b_tgt = QPushButton("Find Required Overpayment"); b_tgt.clicked.connect(self._calc_target)
        tl.addWidget(b_tgt)
        self.tgt_lbl = QLabel("Required monthly overpayment: —")
        tl.addWidget(self.tgt_lbl); tl.addStretch()
        root.addWidget(tgt)

    def set_params(self, p): self._params = p

    def _run(self):
        if not self._params: return
        p = self._params; scenarios = []
        for i, sp in enumerate(self._spins):
            ov = sp.value()
            c  = MortgageCalc(p["principal"], p["annual_rate"], p["term_months"],
                               p["start_date"], ov, p["lump_sums"],
                               p["rate2"], p["rate2_start_month"])
            s = c.simulate()
            scenarios.append((f"£{ov:,.0f}/mo", s))
            mo_saved = p["term_months"] - len(s)
            intr     = sum(r["interest"] for r in s)
            payoff   = s[-1]["date"].strftime("%b %Y")
            self._scards[i].update(f"£{ov:,.0f}/mo",
                f"Payoff {payoff} | -{mo_saved}mo | Interest £{intr:,.0f}")
        draw_scenarios(self.sc_canvas, scenarios)

    def _calc_target(self):
        if not self._params: return
        p   = self._params
        tgt = int(self.tgt_y.value() * 12)
        req = MortgageCalc.overpayment_for_target(
            p["principal"], p["annual_rate"], p["term_months"], p["start_date"], tgt,
            p["rate2"], p["rate2_start_month"])
        self.tgt_lbl.setText(f"Required monthly overpayment: £{req:,.2f}")

# ─────────────────────────────────────────────
#  SCHEDULE TAB
# ─────────────────────────────────────────────
class ScheduleTab(QWidget):
    def __init__(self):
        super().__init__()
        self._sched = []
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14); root.setSpacing(10)

        top = QHBoxLayout()
        self.summary = QLabel(""); self.summary.setObjectName("dim")
        top.addWidget(self.summary); top.addStretch()
        b_csv = QPushButton("Export CSV"); b_csv.setObjectName("secondary")
        b_csv.clicked.connect(self._export); top.addWidget(b_csv)
        root.addLayout(top)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["Month", "Date", "Payment", "Principal", "Interest", "Overpayment", "Balance"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(f"QTableWidget {{ alternate-background-color: {PANEL_BG}; }}")
        root.addWidget(self.table, stretch=1)

    def refresh(self, sched: list):
        self._sched = sched
        self.table.setRowCount(len(sched))
        tp = sum(r["payment"]  for r in sched)
        ti = sum(r["interest"] for r in sched)
        self.summary.setText(f"{len(sched)} payments  |  Total paid: £{tp:,.0f}  |  Total interest: £{ti:,.0f}")

        def item(txt, right=True):
            it = QTableWidgetItem(txt)
            if right: it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            return it

        for i, r in enumerate(sched):
            self.table.setItem(i, 0, item(str(r["month"]), False))
            self.table.setItem(i, 1, item(r["date"].strftime("%b %Y"), False))
            self.table.setItem(i, 2, item(f"£{r['payment']:,.2f}"))
            self.table.setItem(i, 3, item(f"£{r['principal']:,.2f}"))
            self.table.setItem(i, 4, item(f"£{r['interest']:,.2f}"))
            self.table.setItem(i, 5, item(f"£{r['overpayment']:,.2f}"))
            self.table.setItem(i, 6, item(f"£{r['balance']:,.2f}"))

    def _export(self):
        if not self._sched: return
        p = QFileDialog.getSaveFileName(self, "Export Schedule", "amortisation.csv", "CSV (*.csv)")[0]
        if not p: return
        with open(p, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["Month", "Date", "Payment", "Principal", "Interest", "Overpayment", "Balance"])
            for r in self._sched:
                w.writerow([r["month"], r["date"].isoformat(),
                             round(r["payment"],2), round(r["principal"],2),
                             round(r["interest"],2), round(r["overpayment"],2),
                             round(r["balance"],2)])

# ─────────────────────────────────────────────
#  MAIN WINDOW
# ─────────────────────────────────────────────
class MortgageApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mortgage Overpayment Dashboard")
        if LOGO_PATH.exists():
            self.setWindowIcon(QIcon(str(LOGO_PATH)))
        self.resize(1440, 930)
        self.setMinimumSize(1180, 860)
        self._dark_titlebar()

        root = QWidget(); self.setCentralWidget(root)
        ml   = QHBoxLayout(root); ml.setContentsMargins(0, 0, 0, 0); ml.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.calculate_requested.connect(self._calculate)
        ml.addWidget(self.sidebar)

        # Content
        content = QWidget()
        content.setStyleSheet(f"background:{BG_DARK};")
        cl = QVBoxLayout(content); cl.setContentsMargins(0, 0, 0, 0); cl.setSpacing(0)

        # Header
        hdr = QFrame(); hdr.setObjectName("topBar"); hdr.setFixedHeight(52)
        hl  = QHBoxLayout(hdr); hl.setContentsMargins(18, 0, 18, 0)
        htitle = QLabel("Mortgage Overpayment Dashboard")
        htitle.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        hl.addWidget(htitle); hl.addStretch()
        self.status = QLabel("Enter mortgage details and press Calculate")
        self.status.setObjectName("dim")
        hl.addWidget(self.status)
        cl.addWidget(hdr)

        # Tabs
        self.tabs = QTabWidget()
        self.t_dash = DashboardTab()
        self.t_anal = AnalysisTab()
        self.t_scen = ScenariosTab()
        self.t_sched= ScheduleTab()
        self.tabs.addTab(self.t_dash,  "  Dashboard  ")
        self.tabs.addTab(self.t_anal,  "  Analysis  ")
        self.tabs.addTab(self.t_scen,  "  Scenarios  ")
        self.tabs.addTab(self.t_sched, "  Schedule  ")
        cl.addWidget(self.tabs, stretch=1)
        ml.addWidget(content, stretch=1)

    def _dark_titlebar(self):
        try:
            import ctypes
            hwnd = int(self.winId())
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 20, ctypes.byref(ctypes.c_int(1)), ctypes.sizeof(ctypes.c_int))
        except Exception:
            pass

    def _calculate(self):
        try:
            params = self.sidebar.get_params()
            if params["principal"] <= 0:
                QMessageBox.warning(self, "Input error", "Loan amount must be greater than zero.")
                return
            self.status.setText("Calculating…")
            QApplication.processEvents()

            calc_base = MortgageCalc(
                params["principal"], params["annual_rate"], params["term_months"],
                params["start_date"],
                rate2=params["rate2"], rate2_start_month=params["rate2_start_month"])
            base = calc_base.simulate_base()

            calc_op = MortgageCalc(
                params["principal"], params["annual_rate"], params["term_months"],
                params["start_date"], params["monthly_overpay"], params["lump_sums"],
                params["rate2"], params["rate2_start_month"])
            op = calc_op.simulate()

            self.t_dash.refresh(params, base, op)
            self.t_anal.refresh(base, op)
            self.t_scen.set_params(params); self.t_scen._run()
            self.t_sched.refresh(op)

            months_saved = len(base) - len(op)
            payoff = op[-1]["date"].strftime("%b %Y")
            self.status.setText(
                f"Done  |  Payoff: {payoff}  |  {len(op)} payments  |  "
                f"{months_saved} months saved ({months_saved//12}y {months_saved%12}m)"
            )
        except Exception as ex:
            QMessageBox.critical(self, "Error", str(ex))
            self.status.setText("Error — check inputs")

# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    if LOGO_PATH.exists():
        app.setWindowIcon(QIcon(str(LOGO_PATH)))
    app.setStyleSheet(stylesheet())
    win = MortgageApp()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
