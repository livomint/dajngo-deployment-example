set terminal png
set xlabel 'range'
set ylabel 'density'
set output '/home2/jcjeong/project/stanalyzer0/stanalyzer/media/jcjeong/20131002153036015885WTZumI/density_custom/density_custom0.png'
plot "/home2/jcjeong/project/stanalyzer0/stanalyzer/media/jcjeong/20131002153036015885WTZumI/density_custom/density_carbonyl.dat" using 1:2 title "Density" with lines lw 3