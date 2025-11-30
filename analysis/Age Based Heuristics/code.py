import mpmath as mp
import matplotlib.pyplot as plt
import pandas as pd

# Model Parameters
k = 19.28                   # Gamma shape
rate = 1.61
theta = 1 / rate           # Gamma scale
T = 12.0                   # Max age for triangular decoy distribution

# https://www.getmonero.org/resources/moneropedia/block.html
# age_days = (spend_height - origin_height) / 720
# Monero target block time = 2 minutes for every block
# 1 hour -> 30 blocks per hour
# 24 hours -> 30 * 24 = 720 blocks per day
# Hence, assuming 720 blocks/day
# List of ring member ages in days from pos 0 to 15
ages = [
    11.47, 4.87, 2.82, 2.11, 1.78, 1.30,
    0.88, 0.84, 0.53, 0.51, 0.50, 0.50,
    0.34, 0.31, 0.15, 0.12
]


# Gamma PDF function
def gamma_pdf(x, k, theta):
    """Silent Gamma PDF (used in probability calculations)."""
    return float((x**(k-1) * mp.e**(-x/theta)) / (mp.gamma(k) * theta**k))

# Until Early 2017, Monero utilized a triangular decoy distribution to select decoy ages
# triangular DM function
def dm_triangular(x, T):
    """Silent triangular PDF (old Monero decoy sampling)."""
    if x < 0 or x > T:
        return 0
    return 2 * (T - x) / (T * T)

# A more verbose version for gamma PDF computation

def gamma_pdf_verbose(x, k, theta):
    print("\n=== Gamma PDF Computation ===")
    print(f"x = {x}")
    print(f"k = {k}")
    print(f"theta = {theta}")

    # Step 1: x^(k-1)
    x_pow = x**(k-1)
    print(f"x^(k-1) = {x_pow:e}")

    # Step 2: exp(-x/theta)
    exp_term = mp.e**(-x/theta)
    print(f"exp(-x/theta) = {exp_term:e}")
    print(f"  where -x/theta = {-x/theta}")

    # Step 3: Gamma(k)
    gamma_k = mp.gamma(k)
    print(f"Gamma(k) = {gamma_k:e}")

    # Step 4: theta^k
    theta_pow = theta**k
    print(f"theta^k = {theta_pow:e}")

    # Final PDF
    pdf = (x_pow * exp_term) / (gamma_k * theta_pow)
    print(f"\nGamma PDF f(x) = {pdf:e}\n")

    return float(pdf)

def dm_triangular_verbose(x, T):
    print("\n=== Triangular DM Computation ===")
    print(f"x = {x}")
    print(f"T = {T}")

    if x < 0 or x > T:
        print("x is outside [0, T] → DM = 0")
        return 0

    numerator = 2 * (T - x)
    denominator = T * T
    dm = numerator / denominator

    print(f"DM = 2*(T - x)/(T*T)")
    print(f"    = 2*({T} - {x})/{T*T}")
    print(f"    = {numerator}/{denominator}")
    print(f"    = {dm}\n")

    return dm

# COMPUTE DS, DM, RATIOS, PROBABILITIES

DS = [gamma_pdf(a, k, theta) for a in ages]   # Call Gamma PDF function
DM = [dm_triangular(a, T) for a in ages]    # Call Triangular DM function

ratios = [ds / dm for ds, dm in zip(DS, DM)]   # temporal attack
total_ratio = sum(ratios)
P_old = [r / total_ratio for r in ratios]      # OLD Monero P(real)
P_new = [1/16] * 16                             # MODERN Monero P(real)

# -----------------------------
# BUILD TABLE
# -----------------------------
df = pd.DataFrame({
    "position": list(range(16)),
    "age_days": ages,
    "DS_gamma": DS,
    "DM_triangular": DM,
    "ratio_DS_DM": ratios,
    "P_old_2017": P_old,
    "P_new_modern": P_new
})
pd.set_option('display.float_format', lambda x: f"{x:.12e}")
print(df)

# Graph 1: DS vs DM

plt.figure(figsize=(8,5))
plt.plot(ages, DS, marker='o', label='DS (Gamma)')
plt.plot(ages, DM, marker='x', label='DM (Triangular)')
plt.xlabel("Age (days)")
plt.ylabel("Value")
plt.title("DS (Gamma) vs DM (Triangular)")
plt.grid(True)
plt.legend()
plt.show()

# Graph 2: DS/DM Ratio

plt.figure(figsize=(8,5))
plt.plot(ages, ratios, marker='o', color='orange')
plt.xlabel("Age (days)")
plt.ylabel("DS/DM Ratio")
plt.title("DS/DM Ratio per Ring Member")
plt.grid(True)
plt.show()


# Graph 3: Old vs Modern Monero Probabilities

plt.figure(figsize=(8,5))
plt.plot(range(16), P_old, marker='o', label='OLD (2017) P(real)')
plt.plot(range(16), P_new, marker='x', label='MODERN (2025) P(real)')
plt.xlabel("Ring Position")
plt.ylabel("Probability")
plt.title("Old vs Modern Monero Posterior Probabilities")
plt.grid(True)
plt.legend()
plt.show()
