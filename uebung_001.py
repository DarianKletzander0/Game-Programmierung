summe = 0

for zahl in range(437, 32483):
    summe += zahl

print("Summe von 437 bis 32482:", summe)


def teile_kleineren_durch_groesseren(wert_1: float, wert_2: float) -> float:
    if wert_1 > wert_2:
        return wert_2 / wert_1
    elif wert_2 > wert_1:
        return wert_1 / wert_2
    else:
        return 1.0


print("Test 1:", teile_kleineren_durch_groesseren(10.0, 5.0))
print("Test 2:", teile_kleineren_durch_groesseren(3.5, 7.0))
print("Test 3:", teile_kleineren_durch_groesseren(4.0, 4.0))
print("Test 4:", teile_kleineren_durch_groesseren(12.0, 2.5))
