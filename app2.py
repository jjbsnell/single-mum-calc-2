
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# ============================================================
# SINGLE PARENT FINANCIAL MODEL
# 2026/27 — GREATER LONDON
# Streamlit version
# ============================================================

st.set_page_config(
    page_title="Single Parent Financial Model",
    page_icon="£",
    layout="wide",
)

# ============================================================
# 1. FIXED 2026/27 RATES
# ============================================================

PERSONAL_ALLOWANCE = 12_570
BASIC_RATE_BAND = 37_700
HIGHER_RATE_THRESHOLD = 50_270
ADDITIONAL_RATE_THRESHOLD = 125_140

BASIC_RATE = 0.20
HIGHER_RATE = 0.40
ADDITIONAL_RATE = 0.45

EMPLOYEE_NI_PRIMARY_THRESHOLD = 12_570
EMPLOYEE_NI_UPPER_LIMIT = 50_270
EMPLOYEE_NI_MAIN_RATE = 0.08
EMPLOYEE_NI_UPPER_RATE = 0.02

SE_CLASS4_LOWER_LIMIT = 12_570
SE_CLASS4_UPPER_LIMIT = 50_270
SE_CLASS4_MAIN_RATE = 0.06
SE_CLASS4_UPPER_RATE = 0.02

UC_STANDARD_ALLOWANCE = 424.90
UC_CHILD_ELEMENT = 303.94
UC_TAPER = 0.55
UC_WORK_ALLOWANCE_HOUSING = 427.00
UC_WORK_ALLOWANCE_NO_HOUSING = 710.00

UC_CAPITAL_DISREGARD = 6_000
UC_CAPITAL_LIMIT = 16_000
UC_TARIFF_RATE = 4.35

BENEFIT_CAP_GREATER_LONDON = 2_110.25
BENEFIT_CAP_EARNINGS_THRESHOLD = 881.00

CHILD_BENEFIT_WEEKLY = 27.05
CHILD_BENEFIT_ANNUAL = CHILD_BENEFIT_WEEKLY * 52
CHILD_BENEFIT_MONTHLY = CHILD_BENEFIT_ANNUAL / 12

CHILD_BENEFIT_HIC_START = 60_000
CHILD_BENEFIT_HIC_FULL = 80_000

LHA_1_BED_WEEKLY = 331.39
LHA_2_BED_WEEKLY = 412.86
LHA_1_BED = LHA_1_BED_WEEKLY * 52 / 12
LHA_2_BED = LHA_2_BED_WEEKLY * 52 / 12

MINIMUM_SUPPORT = 400.00

NATIONAL_LIVING_WAGE = 12.71
MIF_HOURS_PER_WEEK = 35
MIF_WEEKS_PER_YEAR = 52


# ============================================================
# 2. HELPERS
# ============================================================

def money(x):
    return f"£{x:,.0f}"


def money2(x):
    return f"£{x:,.2f}"


def calculate_income_tax(gross):
    gross = max(0, gross)

    if gross <= 100_000:
        allowance = PERSONAL_ALLOWANCE
    else:
        allowance_reduction = (gross - 100_000) / 2
        allowance = max(0, PERSONAL_ALLOWANCE - allowance_reduction)

    taxable = max(0, gross - allowance)

    basic_taxable = min(taxable, BASIC_RATE_BAND)
    basic_tax = basic_taxable * BASIC_RATE

    higher_band_limit = max(0, ADDITIONAL_RATE_THRESHOLD - allowance)
    higher_taxable = max(
        0,
        min(taxable, higher_band_limit) - BASIC_RATE_BAND
    )
    higher_tax = higher_taxable * HIGHER_RATE

    additional_taxable = max(0, taxable - higher_band_limit)
    additional_tax = additional_taxable * ADDITIONAL_RATE

    return {
        "allowance": allowance,
        "taxable": taxable,
        "total": basic_tax + higher_tax + additional_tax,
    }


def calculate_employee_ni(gross):
    gross = max(0, gross)

    main_band = min(
        max(0, gross - EMPLOYEE_NI_PRIMARY_THRESHOLD),
        EMPLOYEE_NI_UPPER_LIMIT - EMPLOYEE_NI_PRIMARY_THRESHOLD,
    )

    upper_band = max(0, gross - EMPLOYEE_NI_UPPER_LIMIT)

    main_ni = main_band * EMPLOYEE_NI_MAIN_RATE
    upper_ni = upper_band * EMPLOYEE_NI_UPPER_RATE

    return {
        "total": main_ni + upper_ni,
        "main": main_ni,
        "upper": upper_ni,
    }


def calculate_self_employed_ni(profit):
    profit = max(0, profit)

    main_band = min(
        max(0, profit - SE_CLASS4_LOWER_LIMIT),
        SE_CLASS4_UPPER_LIMIT - SE_CLASS4_LOWER_LIMIT,
    )

    upper_band = max(0, profit - SE_CLASS4_UPPER_LIMIT)

    main_ni = main_band * SE_CLASS4_MAIN_RATE
    upper_ni = upper_band * SE_CLASS4_UPPER_RATE

    return {
        "total": main_ni + upper_ni,
        "main": main_ni,
        "upper": upper_ni,
    }


def calculate_employed_income(monthly_gross):
    annual_gross = monthly_gross * 12
    tax = calculate_income_tax(annual_gross)
    ni = calculate_employee_ni(annual_gross)

    annual_net = annual_gross - tax["total"] - ni["total"]

    return {
        "annual_gross": annual_gross,
        "annual_tax": tax["total"],
        "annual_ni": ni["total"],
        "monthly_tax": tax["total"] / 12,
        "monthly_ni": ni["total"] / 12,
        "monthly_net": annual_net / 12,
        "tax": tax,
        "ni": ni,
    }


def calculate_self_employed_income(monthly_turnover, monthly_expenses):
    annual_turnover = monthly_turnover * 12
    annual_expenses = monthly_expenses * 12
    annual_profit = max(0, annual_turnover - annual_expenses)

    tax = calculate_income_tax(annual_profit)
    ni = calculate_self_employed_ni(annual_profit)

    annual_net = annual_profit - tax["total"] - ni["total"]

    return {
        "annual_turnover": annual_turnover,
        "annual_expenses": annual_expenses,
        "annual_profit": annual_profit,
        "annual_tax": tax["total"],
        "annual_ni": ni["total"],
        "monthly_profit": annual_profit / 12,
        "monthly_tax": tax["total"] / 12,
        "monthly_ni": ni["total"] / 12,
        "monthly_net": annual_net / 12,
        "tax": tax,
        "ni": ni,
    }


def calculate_mif():
    gross_annual = (
        NATIONAL_LIVING_WAGE
        * MIF_HOURS_PER_WEEK
        * MIF_WEEKS_PER_YEAR
    )
    gross_monthly = gross_annual / 12

    tax = calculate_income_tax(gross_annual)
    ni = calculate_employee_ni(gross_annual)

    net_annual = gross_annual - tax["total"] - ni["total"]

    return {
        "gross_annual": gross_annual,
        "gross_monthly": gross_monthly,
        "net_annual": net_annual,
        "net_monthly": net_annual / 12,
    }


def calculate_child_benefit(adjusted_net_income):
    if adjusted_net_income <= CHILD_BENEFIT_HIC_START:
        charge = 0
    elif adjusted_net_income >= CHILD_BENEFIT_HIC_FULL:
        charge = CHILD_BENEFIT_ANNUAL
    else:
        excess = adjusted_net_income - CHILD_BENEFIT_HIC_START
        charge = CHILD_BENEFIT_ANNUAL * (excess / 20_000)

    net_annual = CHILD_BENEFIT_ANNUAL - charge

    return {
        "gross_annual": CHILD_BENEFIT_ANNUAL,
        "charge": charge,
        "net_annual": net_annual,
        "net_monthly": net_annual / 12,
    }


def calculate_cms(father_gross_annual, shared_care_nights=0):
    weekly_income = min(max(0, father_gross_annual) / 52, 3_000)

    if weekly_income < 7:
        weekly_cms = 0
        rate = "Nil rate"
    elif weekly_income <= 100:
        weekly_cms = 7
        rate = "Flat rate"
    elif weekly_income < 200:
        weekly_cms = 7 + 0.17 * (weekly_income - 100)
        rate = "Reduced rate"
    elif weekly_income <= 800:
        weekly_cms = weekly_income * 0.12
        rate = "Basic rate"
    else:
        weekly_cms = 800 * 0.12 + (weekly_income - 800) * 0.09
        rate = "Basic Plus"

    if 52 <= shared_care_nights <= 103:
        weekly_cms *= 6 / 7
    elif 104 <= shared_care_nights <= 155:
        weekly_cms *= 5 / 7
    elif 156 <= shared_care_nights <= 174:
        weekly_cms *= 4 / 7
    elif shared_care_nights >= 175:
        weekly_cms *= 0.5
        weekly_cms = max(0, weekly_cms - 7)

    monthly_cms = weekly_cms * 52 / 12
    support = max(MINIMUM_SUPPORT, monthly_cms)

    return {
        "weekly_income": weekly_income,
        "weekly_cms": weekly_cms,
        "monthly_cms": monthly_cms,
        "support": support,
        "rate": rate,
    }


def get_lha(bedrooms):
    return LHA_1_BED if bedrooms == 1 else LHA_2_BED


def calculate_capital_tariff(savings):
    if savings <= UC_CAPITAL_DISREGARD:
        return 0

    if savings > UC_CAPITAL_LIMIT:
        return None

    excess = savings - UC_CAPITAL_DISREGARD
    units = np.ceil(excess / 250)

    return units * UC_TARIFF_RATE


def calculate_uc(
    net_earnings,
    rent,
    bedrooms,
    savings,
    child_present,
    apply_mif=False,
    mif_net_monthly=0,
):
    capital_tariff = calculate_capital_tariff(savings)

    if capital_tariff is None:
        return {
            "eligible": False,
            "maximum_uc": 0,
            "housing_element": 0,
            "work_allowance": 0,
            "earnings_used": net_earnings,
            "earnings_deduction": 0,
            "capital_tariff": 0,
            "uc_before_cap": 0,
            "mif": 0,
        }

    lha = get_lha(bedrooms)
    housing_element = min(rent, lha)

    maximum_uc = UC_STANDARD_ALLOWANCE + housing_element

    if child_present:
        maximum_uc += UC_CHILD_ELEMENT

    if apply_mif:
        earnings_used = max(net_earnings, mif_net_monthly)
    else:
        earnings_used = net_earnings

    work_allowance = (
        UC_WORK_ALLOWANCE_HOUSING
        if housing_element > 0
        else UC_WORK_ALLOWANCE_NO_HOUSING
    )

    earnings_above_allowance = max(
        0,
        earnings_used - work_allowance,
    )

    earnings_deduction = earnings_above_allowance * UC_TAPER

    uc_before_cap = max(
        0,
        maximum_uc - earnings_deduction - capital_tariff,
    )

    return {
        "eligible": True,
        "maximum_uc": maximum_uc,
        "housing_element": housing_element,
        "work_allowance": work_allowance,
        "earnings_used": earnings_used,
        "earnings_deduction": earnings_deduction,
        "capital_tariff": capital_tariff,
        "uc_before_cap": uc_before_cap,
        "mif": mif_net_monthly if apply_mif else 0,
    }


def calculate_household(
    mother_income,
    employment_type,
    business_expenses,
    startup_period,
    gainfully_self_employed,
    rent,
    bedrooms,
    savings,
    other_disregarded_cash,
    father_income,
    shared_care_nights,
    child_present,
    council_tax,
    utilities,
    food,
    baby_costs,
    transport,
):
    if employment_type == "employed":
        work = calculate_employed_income(mother_income)
        net_work_income = work["monthly_net"]
        uc_earnings = work["monthly_net"]
        mif_applies = False
        mif = None
    else:
        work = calculate_self_employed_income(
            mother_income,
            business_expenses,
        )
        net_work_income = work["monthly_net"]
        uc_earnings = work["monthly_net"]
        mif = calculate_mif()
        mif_applies = gainfully_self_employed and not startup_period

    cms = calculate_cms(
        father_gross_annual=father_income,
        shared_care_nights=shared_care_nights,
    )
    support = cms["support"]

    mif_amount = mif["net_monthly"] if mif_applies else 0

    uc = calculate_uc(
        net_earnings=uc_earnings,
        rent=rent,
        bedrooms=bedrooms,
        savings=savings,
        child_present=child_present,
        apply_mif=mif_applies,
        mif_net_monthly=mif_amount,
    )

    if child_present:
        cb_income = (
            work["annual_gross"]
            if employment_type == "employed"
            else work["annual_profit"]
        )
        child_benefit = calculate_child_benefit(cb_income)
    else:
        child_benefit = {
            "gross_annual": 0,
            "charge": 0,
            "net_annual": 0,
            "net_monthly": 0,
        }

    child_benefit_monthly = child_benefit["net_monthly"]

    cap_test_earnings = net_work_income
    cap_exempt = cap_test_earnings >= BENEFIT_CAP_EARNINGS_THRESHOLD

    benefit_cap_applies = child_present and not cap_exempt

    benefits_before_cap = uc["uc_before_cap"] + child_benefit_monthly

    if benefit_cap_applies:
        benefit_cap_reduction = max(
            0,
            benefits_before_cap - BENEFIT_CAP_GREATER_LONDON,
        )
    else:
        benefit_cap_reduction = 0

    actual_uc = max(
        0,
        uc["uc_before_cap"] - benefit_cap_reduction,
    )

    total_benefits = actual_uc + child_benefit_monthly

    total_income = (
        net_work_income
        + total_benefits
        + support
        + other_disregarded_cash
    )

    lha = get_lha(bedrooms)
    rent_above_lha = max(0, rent - lha)

    household_costs = (
        council_tax
        + utilities
        + food
        + baby_costs
        + transport
    )

    total_outgoings = rent + household_costs
    disposable = total_income - total_outgoings

    return {
        "work": work,
        "net_work_income": net_work_income,
        "uc_earnings": uc_earnings,
        "mif": mif,
        "mif_applies": mif_applies,
        "cms": cms,
        "support": support,
        "uc": uc,
        "child_benefit": child_benefit,
        "child_benefit_monthly": child_benefit_monthly,
        "total_benefits": total_benefits,
        "cap_test_earnings": cap_test_earnings,
        "cap_exempt": cap_exempt,
        "benefit_cap_applies": benefit_cap_applies,
        "benefits_before_cap": benefits_before_cap,
        "benefit_cap_reduction": benefit_cap_reduction,
        "actual_uc": actual_uc,
        "lha": lha,
        "rent_above_lha": rent_above_lha,
        "household_costs": household_costs,
        "total_outgoings": total_outgoings,
        "total_income": total_income,
        "disposable": disposable,
    }


# ============================================================
# UI
# ============================================================

st.title("Single Parent Financial Model")
st.caption("2026/27 Greater London scenario")

st.info(
    "This is a planning model, not an official DWP, HMRC or "
    "Child Maintenance Service calculation."
)

with st.sidebar:
    st.header("Scenario")

    stage = st.radio(
        "Stage",
        ["Pregnant / before birth", "Baby born"],
        index=1,
    )

    bedrooms = st.radio(
        "Property size being modelled",
        [1, 2],
        index=1,
        format_func=lambda x: f"{x} bedroom",
    )

    employment_type = st.radio(
        "Work status",
        ["Employed", "Self-employed"],
        horizontal=True,
    )

    st.header("Her circumstances")

    mother_income = st.slider(
        "Her monthly income (pre-tax)",
        min_value=0,
        max_value=6000,
        value=0,
        step=25,
    )

    if employment_type == "Self-employed":
        business_expenses = st.slider(
            "Monthly business expenses",
            min_value=0,
            max_value=4000,
            value=0,
            step=25,
        )

        startup_period = st.radio(
            "12-month self-employed start-up period",
            ["No", "Yes"],
            horizontal=True,
        ) == "Yes"

        gainfully_self_employed = st.radio(
            "Gainfully self-employed",
            ["No", "Yes"],
            horizontal=True,
        ) == "Yes"
    else:
        business_expenses = 0
        startup_period = False
        gainfully_self_employed = False

    savings = st.slider(
        "Her savings",
        min_value=0,
        max_value=30_000,
        value=0,
        step=250,
    )

    other_disregarded_cash = st.slider(
        "Other genuinely UC-disregarded cash",
        min_value=0,
        max_value=3000,
        value=0,
        step=25,
        help=(
            "Only use this for money which genuinely has no "
            "UC earnings treatment. Do not use it for "
            "undeclared taxable earnings."
        ),
    )

    st.header("His circumstances")

    father_income = st.slider(
        "His gross annual income",
        min_value=0,
        max_value=250_000,
        value=40_000,
        step=1000,
    )

    shared_care = st.selectbox(
        "Shared care",
        [
            ("0 nights", 0),
            ("52–103 nights", 52),
            ("104–155 nights", 104),
            ("156–174 nights", 156),
            ("175+ nights", 175),
        ],
        format_func=lambda x: x[0],
    )
    shared_care_nights = shared_care[1]

    st.header("Housing")

    rent = st.slider(
        "Monthly rent",
        min_value=500,
        max_value=3500,
        value=1500,
        step=25,
    )

    st.header("Monthly household costs")

    council_tax = st.slider(
        "Council tax",
        min_value=0,
        max_value=500,
        value=0,
        step=10,
    )

    utilities = st.slider(
        "Utilities",
        min_value=0,
        max_value=700,
        value=200,
        step=10,
    )

    food = st.slider(
        "Food",
        min_value=0,
        max_value=1200,
        value=300,
        step=25,
    )

    baby_costs = st.slider(
        "Baby costs",
        min_value=0,
        max_value=1000,
        value=150,
        step=25,
    )

    transport = st.slider(
        "Transport",
        min_value=0,
        max_value=600,
        value=100,
        step=25,
    )

child_present = stage == "Baby born"

result = calculate_household(
    mother_income=mother_income,
    employment_type=employment_type.lower().replace("-", "_"),
    business_expenses=business_expenses,
    startup_period=startup_period,
    gainfully_self_employed=gainfully_self_employed,
    rent=rent,
    bedrooms=bedrooms,
    savings=savings,
    other_disregarded_cash=other_disregarded_cash,
    father_income=father_income,
    shared_care_nights=shared_care_nights,
    child_present=child_present,
    council_tax=council_tax,
    utilities=utilities,
    food=food,
    baby_costs=baby_costs,
    transport=transport,
)

# ============================================================
# TOP SUMMARY
# ============================================================

st.subheader("Current household position")

cols = st.columns(4)

cols[0].metric(
    "Net work income",
    money(result["net_work_income"]),
    help="Per month after Income Tax and applicable NI.",
)

cols[1].metric(
    "Total benefits",
    money(result["total_benefits"]),
    help="Universal Credit after any Benefit Cap reduction + Child Benefit.",
)

cols[2].metric(
    "CMS / support",
    money(result["support"]),
)

cols[3].metric(
    "Money left",
    money(result["disposable"]),
)

cols2 = st.columns(4)

cols2[0].metric("Universal Credit", money(result["actual_uc"]))
cols2[1].metric("Child Benefit", money(result["child_benefit_monthly"]))
cols2[2].metric("Monthly rent", money(rent))
cols2[3].metric("Monthly household costs", money(result["household_costs"]))

# ============================================================
# WORK INCOME
# ============================================================

with st.expander("Income tax & National Insurance", expanded=False):
    work = result["work"]

    if employment_type == "Employed":
        st.write(f"Annual gross: **{money(work['annual_gross'])}**")
        st.write(f"Income Tax: **-{money(work['annual_tax'])}**")
        st.write(f"Employee NI: **-{money(work['annual_ni'])}**")
        st.write(
            f"Annual net: **{money(work['annual_gross'] - work['annual_tax'] - work['annual_ni'])}**"
        )
    else:
        st.write(f"Annual turnover: **{money(work['annual_turnover'])}**")
        st.write(f"Business expenses: **-{money(work['annual_expenses'])}**")
        st.write(f"Annual profit: **{money(work['annual_profit'])}**")
        st.write(f"Income Tax: **-{money(work['annual_tax'])}**")
        st.write(f"Class 4 NI: **-{money(work['annual_ni'])}**")
        st.write(
            f"Annual net: **{money(work['annual_profit'] - work['annual_tax'] - work['annual_ni'])}**"
        )

# ============================================================
# TOTAL BENEFITS
# ============================================================

st.subheader("Total benefits")

benefit_cols = st.columns(3)

benefit_cols[0].metric(
    "Universal Credit",
    money(result["actual_uc"]),
)

benefit_cols[1].metric(
    "Child Benefit",
    money(result["child_benefit_monthly"]),
)

benefit_cols[2].metric(
    "TOTAL BENEFITS",
    money(result["total_benefits"]),
)

# ============================================================
# UC
# ============================================================

with st.expander("Universal Credit", expanded=False):
    uc = result["uc"]

    st.write(f"Standard allowance: **{money(UC_STANDARD_ALLOWANCE)}**")

    st.write(
        f"Child element: **{money(UC_CHILD_ELEMENT if child_present else 0)}**"
    )

    st.write(
        f"Housing element: **{money(uc['housing_element'])}**"
    )

    st.write(
        f"Maximum UC before earnings: **{money(uc['maximum_uc'])}**"
    )

    st.write(
        f"Work allowance: **{money(uc['work_allowance'])}**"
    )

    st.write(
        f"Net earnings used by UC: **{money(uc['earnings_used'])}**"
    )

    st.write(
        f"55% earnings deduction: **-{money(uc['earnings_deduction'])}**"
    )

    st.write(
        f"Capital tariff: **-{money(uc['capital_tariff'])}**"
    )

    if not uc["eligible"]:
        st.error(
            "Savings exceed £16,000, so the model assumes no Universal Credit."
        )
    else:
        st.write(
            f"UC before Benefit Cap: **{money(uc['uc_before_cap'])}**"
        )

# ============================================================
# BENEFIT CAP
# ============================================================

with st.expander("Benefit Cap", expanded=False):

    if result["cap_exempt"]:
        st.success("The £881 net-earnings test is reached, so the model does not apply the Benefit Cap.")
    elif result["benefit_cap_applies"]:
        st.warning("The Benefit Cap is applying in this scenario.")
    else:
        st.info("The Benefit Cap is not applying in this scenario.")

    st.write(
        f"Net earnings for £881 test: **{money(result['cap_test_earnings'])}**"
    )
    st.write(
        f"Earnings exemption threshold: **{money(BENEFIT_CAP_EARNINGS_THRESHOLD)}**"
    )
    st.write(
        f"Greater London Benefit Cap: **{money(BENEFIT_CAP_GREATER_LONDON)} / month**"
    )
    st.write(
        f"UC before cap: **{money(result['uc']['uc_before_cap'])}**"
    )
    st.write(
        f"Child Benefit: **{money(result['child_benefit_monthly'])}**"
    )
    st.write(
        f"UC + Child Benefit before cap: **{money(result['benefits_before_cap'])}**"
    )
    st.write(
        f"Benefit Cap reduction: **-{money(result['benefit_cap_reduction'])}**"
    )

    st.caption(
        "Child Benefit counts towards the Benefit Cap. The Child Benefit "
        "payment itself is not reduced; where the cap applies, the "
        "reduction is taken from a capped benefit such as Universal Credit."
    )

# ============================================================
# HOUSING / LHA
# ============================================================

with st.expander("Housing & LHA", expanded=True):

    st.write(f"Property being modelled: **{bedrooms} bedroom**")
    st.write(f"Modelled LHA rate: **{money(result['lha'])} / month**")
    st.write(f"Monthly rent: **{money(rent)}**")
    st.write(f"Rent above modelled LHA: **{money(result['rent_above_lha'])}**")

    st.warning(
        """
        **LHA bedroom entitlement — important disclaimer**

        The 1-bedroom / 2-bedroom selector represents the **size of
        property being rented**. It does not itself determine the
        claimant's official LHA bedroom entitlement.

        The actual LHA bedroom category is determined by the household's
        circumstances and the applicable bedroom-entitlement rules.

        Broadly, the rules provide one bedroom for each adult couple,
        each other adult aged 16 or over, two children under 10 regardless
        of sex, two children of the same sex under 16, and any other child,
        subject to detailed rules and exceptions.

        **For this scenario:** once the baby is born, a single mother with
        one baby will generally have a **2-bedroom LHA bedroom entitlement**:
        one bedroom for herself and one for the child.

        Therefore, the 2-bedroom scenario corresponds to the household's
        generally applicable bedroom entitlement once the baby is born.

        The 1-bedroom scenario remains available as a comparison showing
        what happens financially if she rents a one-bedroom property. It
        should not be interpreted as saying that she is legally restricted
        to the one-bedroom LHA rate.

        The actual monetary LHA rate depends on the relevant Broad Rental
        Market Area (BRMA), and therefore ultimately on the property's
        postcode. The Central London figures used here are scenario
        assumptions and should be checked against the actual postcode.
        """
    )

# ============================================================
# CMS
# ============================================================

with st.expander("Child Maintenance / support", expanded=False):
    cms = result["cms"]

    st.write(f"His gross annual income: **{money(father_income)}**")
    st.write(f"CMS weekly income: **{money2(cms['weekly_income'])}**")
    st.write(f"CMS calculation band: **{cms['rate']}**")
    st.write(f"Indicative CMS: **{money(cms['monthly_cms'])} / month**")
    st.write(f"Minimum support modelled: **{money(MINIMUM_SUPPORT)} / month**")
    st.write(f"Support included in household income: **{money(result['support'])} / month**")

# ============================================================
# SELF-EMPLOYMENT MIF
# ============================================================

if employment_type == "Self-employed":
    with st.expander("Minimum Income Floor", expanded=False):
        mif = calculate_mif()

        if result["mif_applies"]:
            st.warning("The model is applying the Minimum Income Floor.")
        else:
            st.info("The model is not applying the Minimum Income Floor.")

        st.write(f"Gross monthly equivalent: **{money(mif['gross_monthly'])}**")
        st.write(f"Approximate net monthly equivalent: **{money(mif['net_monthly'])}**")

# ============================================================
# HOUSEHOLD COSTS
# ============================================================

with st.expander("Monthly household costs", expanded=False):
    st.write(f"Council tax: **{money(council_tax)}**")
    st.write(f"Utilities: **{money(utilities)}**")
    st.write(f"Food: **{money(food)}**")
    st.write(f"Baby costs: **{money(baby_costs)}**")
    st.write(f"Transport: **{money(transport)}**")
    st.write(f"Total household costs: **{money(result['household_costs'])}**")

# ============================================================
# GRAPH
# ============================================================

st.subheader("Disposable income vs rent")

earnings_levels = [0, 500, 881, 1200, 1600]
rents = np.linspace(800, 3000, 180)

fig, ax = plt.subplots(figsize=(11, 5.5))

for earnings in earnings_levels:
    disposable_values = []

    for rent_test in rents:
        test_result = calculate_household(
            mother_income=earnings,
            employment_type=employment_type.lower().replace("-", "_"),
            business_expenses=business_expenses,
            startup_period=startup_period,
            gainfully_self_employed=gainfully_self_employed,
            rent=rent_test,
            bedrooms=bedrooms,
            savings=savings,
            other_disregarded_cash=other_disregarded_cash,
            father_income=father_income,
            shared_care_nights=shared_care_nights,
            child_present=child_present,
            council_tax=council_tax,
            utilities=utilities,
            food=food,
            baby_costs=baby_costs,
            transport=transport,
        )
        disposable_values.append(test_result["disposable"])

    ax.plot(
        rents,
        disposable_values,
        linewidth=2,
        label=f"Her income input £{earnings:,.0f}",
    )

ax.axvline(
    result["lha"],
    linestyle="--",
    linewidth=2,
    label=f"Modelled LHA £{result['lha']:,.0f}",
)

ax.axhline(0, linestyle=":", linewidth=1)

ax.set_xlabel("Monthly rent (£)")
ax.set_ylabel("Money left after expenses (£)")
ax.grid(alpha=0.25)
ax.legend()

st.pyplot(fig, use_container_width=True)

# ============================================================
# INFORMATION
# ============================================================

st.subheader("Information & assumptions")

with st.expander("Rules and assumptions", expanded=False):

    st.markdown(
        f"""
### Income Tax — 2026/27

- Personal Allowance: **£12,570**
- Basic rate: **20%**
- Basic-rate band: **£37,700**
- Higher-rate threshold: **£50,270**
- Higher rate: **40%**
- Additional-rate threshold: **£125,140**
- Additional rate: **45%**

### Employee National Insurance

- 8% between £12,570 and £50,270
- 2% above £50,270

### Universal Credit

- Single claimant aged 25+: **£{UC_STANDARD_ALLOWANCE:,.2f}/month**
- Child element: **£{UC_CHILD_ELEMENT:,.2f}/month**
- Work allowance with housing costs: **£{UC_WORK_ALLOWANCE_HOUSING:,.0f}/month**
- Work allowance without housing costs: **£{UC_WORK_ALLOWANCE_NO_HOUSING:,.0f}/month**
- Earnings taper: **55%**

### Benefit Cap — Greater London

- Lone parent with children: **£{BENEFIT_CAP_GREATER_LONDON:,.2f}/month**
- Net earnings test used by this model: **£{BENEFIT_CAP_EARNINGS_THRESHOLD:,.0f}/month**
- Child Benefit counts towards the Benefit Cap.

### Child Benefit

- Only/eldest child: **£{CHILD_BENEFIT_WEEKLY:.2f}/week** in this model.

### Savings and UC

- £6,000 or less: no capital tariff
- £6,000–£16,000: £4.35 per £250 or part thereof
- Above £16,000: normally no Universal Credit

### Central London LHA scenario rates

- 1 bedroom: **£{LHA_1_BED_WEEKLY:.2f}/week**, approximately **£{LHA_1_BED:,.0f}/month**
- 2 bedrooms: **£{LHA_2_BED_WEEKLY:.2f}/week**, approximately **£{LHA_2_BED:,.0f}/month**

### LHA bedroom entitlement

The 1-bedroom / 2-bedroom selector represents the **property being rented**.
It does not itself determine official LHA bedroom entitlement.

Once the baby is born, a single mother with one baby will generally have a
**2-bedroom LHA bedroom entitlement**, subject to the detailed rules.

The actual LHA monetary rate depends on the applicable **BRMA and postcode**.

### Important

This is a planning model, not an official DWP, HMRC or CMS calculation.
Actual entitlement can depend on the claimant's assessment period,
household circumstances, local authority rules and information held by DWP.
"""
    )
