1.	Load data into origin via Daten -> aus Datei importieren -> mehrere ASCII -> Hinzufügen -> **Datei auswählen** -> OK -> [Standard setting are fine] -> OK.

2.	Insert „Langname“ row with the following labels: ~Time[h]	DataSet 	Date	Time	t-Step[h]	t-Set[h]	t-Cyc[h] 	Line	Command	U[V]	I[A]	Ah[Ah]	Ah-Cyc-Charge-0	Ah-Cyc-Discharge-0	Ah-Step 	Ah-Set	Ah-Ch-Set	Ah-Dis-Set	Wh[Wh/kg]	T1[°C]	R-DC	Cyc-Count	Count	State


3.	Create second worksheet with experimental data: Project explorer -> **right-click on empty space** -> new window -> worksheet.

4.	 label it “Experimental” as short- and long name, insert header of the raw data ASCII file into the “Experimental” worksheet.

5.	Create two copies of the original raw worksheet – one will be used for the dQ_dU plots, the other for the RC and Cycling stability testing. Neme them accordingly!

6.	Select the RC-Testing / cyling stability sheet. We only need the values at the end of each cycle. The rows with the values at the end of each cycle all have the state “2”. So we need to sort the WORKSHEET (not the column!!!, right click on the “state” header and then select “sort worksheet”) in ascending or descending order and delete all rows that are not labeled with the state “2” (end of cycle values).

a.	We also want to only look at the values for the discharge steps, so we need to delete all rows that are charge steps. To do this, we again sort the WORKSHEET via the “command” column and delete all entries which are not “discharge”.

b.	Now there is a problem with consecutive labeling of the cycles, as each C-rate step starts with a fresh cycle count. To solve this, we give each cycle a consecutive number. Just mark the first 3 cycle entries “1 2 3” and then drag the box around them down until the end of the column. In our case, we should end at 1030, as there are 10x3 cycles for RC testing and 1000 cycles stability testing.

c.	Now we can plot the RC test figure. The capacities for each cycle are listed as “Ah-Cyc-Dis-0”, so we copy this column to the right end of the worksheet. After this, we set the “Cyc-Count” column as a second X-column (right click on column header -> “set as… -> X”).

d.	As the Discharge capacity is only listed as absolute capacity in Ah, we need to calculate the specific capacity in mAh g-1. This is done by dividing the value by the weight of the ACTIVE MATERIAL in the electrode we used for this measurement in grams (g) and multiplying by a factor of 1000 to switch from Ah to mAh. This can be done via the “F(x)=” - field below the column header. Insert = “Ah-Cyc-Dircharge-0”-Column*1000/[AM weight in g]. 

e.	We can now plot both the RC plots (Cycles 1-30) and the Cycling Stability plots (cycles 31-1030) by using the Cyc-Count column as x-axis and the calculated Discharge capacity [mAh g-1] column as y-axis.

f.	We can add a second layer with the same cyc-count x-axis and the temperature as left y-axis, so we get the temperature at the end of each cycle, too. First, we must copy the Temperature column to an additional column behind the new secondary “cyc-count” x-axis. Then we can add a new layer by right clicking into the graph and select “new layer(axis)” -> “right y (linked x-axis and dimensions)”. In the object manager on the right, we can now select the new layer and open the layer content window (F12). Here, we select the temperature column we just created.


7.	Select the dQ_dU plot sheet. First, we must decide which half-cycle we want to analyze. We should make a copy of the worksheet for every half-cycle. We must delete all the rows that are not part of this half-cycle. In our case, we only want to look at the 2nd discharge cycle of the C/10 test set. We start by deleting all rows with the command “pause” or the cyc-count “0”, which are related to the OCV-phase before cycling. Afterward, we delete the first full cycle (because of the SEI formation) and the first half cycle of the 2nd cycle, identified by the command “charge”. We only want to keep the rows with cyc-count “2” and command “charge”, so we delete all the rows afterwards, too.

a.	Create a new worksheet, copying only the U / V and Ah-Cyc-Discharge-0 columns. This way, the U-column will be the new x. Then we have to extrapolate the U and Discharge values. First, we create a new column which we call “U as y” and give it the function F(x)=A (the original U-column). Then we can extrapolate this fresh U Column by marking it and selecting Analyze -> Mathematik -> Interpolieren/Extrapolieren -> Dialog öffnen. In the Dialogue, insert a fixed number of steps, e.g. 333. Press ok. Note the number of steps in the “Kommentar” field of the column.

b.	Now we create a new column, as before, label it “U as x”, and define the F(x) in this new column to be the values from the “U as y”- column, but don’t set it as x-axis yet.

c.	Extrapolate the Ah-Dis…-Column with the same command as the U column, using the same number of steps.

d.	Differentiate the extrapolated Ah-Dis- values via Analyse -> Mathematik -> Differentieren -> Open Dialog. Press OK.

e.	Now we set the “U as x”-column as actual x-values by marking the column, right clicking on the column header -> Setzen als… -> X. We now have the extrapolated U values set as new x-axis.

f.	We can now plot the dQ_dU graph by selecting the differentiated Ah-Dis column -> Zeichnen -> Liniendiagramm.

g.	We have to label the x-axis correctly as “U [V]” and the y-Axis as “Differential capacity [mAh V-1]”. We also have to change the y-axis scaling by the factor 1000 to get mAh instead of Ah. We do this by double clicking the y-axis, then inserting the value “1000*x” into the “Formel” parameter in the “Beschriftung” subsection.
