# Data Analysis Workflow for Galvanostatic Measurements and dQ/dU Plots

## 1. Worksheet Preparation

- Insert a header row with column labels:
  ```
  ~Time[h], DataSet, Date, Time, t-Step[h], t-Set[h], t-Cyc[h], Line, Command,
  U[V], I[A], Ah[Ah], Ah-Cyc-Charge-0, Ah-Cyc-Discharge-0, Ah-Step,
  Ah-Set, Ah-Ch-Set, Ah-Dis-Set, Wh[Wh/kg], T1[°C], R-DC, Cyc-Count, Count, State
  ```

- Create a second worksheet:
  - Label it “Experimental” (short and long name).
  - Insert the header of the raw ASCII data.

- Make two copies of the original raw worksheet:
  - One for **dQ/dU plots**
  - One for **RC and cycling stability analysis**

## 2. RC and Cycling Stability Analysis

### Data Filtering

- **Filter for end-of-cycle values:**
  - Sort the worksheet by the “State” column.
  - Keep only rows with `State = 2` (end of cycle).

- **Filter for discharge steps:**
  - Sort by the “Command” column.
  - Keep only rows with `Command = discharge`.

### Cycle Label Correction

- The cycle count resets with each C-rate.
- Create a new cycle count column:
  - Manually enter “1 2 3” in first rows.
  - Drag down to fill all values consecutively (should end at 1030 for 10×3 + 1000 cycles).

### Specific Capacity Calculation

- Use the `Ah-Cyc-Dis-0` column (discharge capacity).
- Create a new column for **specific capacity** \([mAh g⁻¹]\):

  \[
  	ext{Specific Capacity} = rac{	ext{Ah-Cyc-Discharge-0} 	imes 1000}{	ext{Active Material Weight [g]}}
  \]

- Set the `Cyc-Count` column as X-axis.

### Plotting

- Plot **RC Test (Cycles 1–30)** and **Cycling Stability (Cycles 31–1030)**:
  - X-axis: `Cyc-Count`
  - Y-axis: Calculated discharge capacity \([mAh g⁻¹]\)

- Add a **temperature plot**:
  - Copy the temperature column next to the cycle count.
  - Add a second layer to the graph:
    - X-axis: same `Cyc-Count`
    - Right Y-axis: Temperature (`T1[°C]`)

## 3. dQ/dU Plot Analysis

### Half-Cycle Selection

- Decide on the half-cycle to analyze.
- Create a copy of the worksheet for that half-cycle.

### Row Filtering

To isolate the **2nd discharge cycle of the C/10 test set**:
- Delete all rows with:
  - `Command = pause`
  - `Cyc-Count = 0` (OCV-phase)
- Delete the first full cycle (SEI formation).
- Keep only rows with:
  - `Cyc-Count = 2`
  - `Command = charge`
- Delete all subsequent rows.
