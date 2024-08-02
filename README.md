


### Wilder
This was certainly one of the more rewarding projects I have been working on. I began implementing this around my freshman year of college. The original version was more rudimentary than anything; meant to satisfy my growing need to create something within the realm of computer science. As my skills were honed in mathematics and computer science, I could pursue more difficult questions and develop a more rigorous algorithm. 

This project consists of two incredibly parts:
1. Backtest Engine
2. Swing Index System

The latter is a technical trading strategy developed in 1978 by J. Welles Wilder Jr. Nowadays, quants have much more sophisticated algorithms. Nevertheless, this proved to be a very challenging and rewarding exercise. What you may notice is the Swing Index System takes
a group of hyperparameters as its inputs. We utilize Bayesian Optimization in an effort to optimize the trading algorithm. This was successfully implemented, but danger arises due to overfitting. For example, optimal parameters may exist on FAANG stocks than American Airlines or Ford. 
Note that this backtest engine is not exhaustive. The virtual brokerage firm we have developed does not account for slippage. It is very rudimentary. Nevertheless, it provides an interesting case for future development. 

A trading engine was attempted, but ultimately discarded. Perhaps in future work it will be developed. 


### Swing Index System
Defined by J. Welles Wilder Jr. in his book, "New Concepts in Technical Trading Systems" written in 1978.

                                                    RULES
                                              SWING INDEX SYSTEM
INITIAL ENTRY

            A. Enter LONG when the ASI crosses **above** the previous significant HSP
            B. Enter SHORT when the ASI crosses **below** the previous significant LSP 

INDEX
STOP AND REVERSE (SAR)
 A. Long      (1) Immediately after being reversed to LONG the SAR is the previous LSP (Anterior SAR)
              (2) Thereafter, the SAR is the **first** LSP after a new HSP is made for the trade (Posterior SAR)
 B. Short     (1) Immediately after being reversed to SHORT the SAR is the previous HSP (Anterior SAR)
              (2) Thereafter, the SAR is the **first** HSP after a new LSP is made for the trade (Posterior SAR)
 
'''



"""

