import logging
import json
import operator
import os.path
import sys
import csv
import unittest
from collections import OrderedDict
import datetime
from datetime import date
from typing import List

from bs4 import BeautifulSoup

from webstkdatafetcher import logic, constants, utility, yahoo_fin_statistics
from selenium import webdriver


class TestYahooFinStatisticsModule(unittest.TestCase):

    def __init__(self, arg):
        super().__init__(arg)
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    def test_start_scraping_yahoo_fin_statistics(self):
        yahoo_fin_statistics.start_scraping_yahoo_fin_statistics(None, False, True, None)

    def test_extract_info_from_stat_html(self):
        test_html = """
            <div id="Col1-0-KeyStatistics-Proxy" data-reactroot="" data-reactid="1" data-react-checksum="-1895638742">
              <section data-test="qsp-statistics" class="Pb(30px) smartphone_Px(20px)" data-yaft-module="tdv2-applet-KeyStatistics" data-reactid="2">
                <div class="C($gray) Fz(xs) Fl(end) smartphone_D(n)" data-reactid="3"><span data-reactid="4">Currency in USD</span></div>
                <div class="Mstart(a) Mend(a)" data-reactid="5">
                  <div class="Fl(start) W(50%) smartphone_W(100%)" data-reactid="6">
                    <h2 class="Pt(20px)" data-reactid="7"><span data-reactid="8">Valuation Measures</span></h2>
                    <div class="Mb(10px) Pend(20px) smartphone_Pend(0px)" data-reactid="9">
                      <div data-reactid="10">
                        <table class="table-qsp-stats Mt(10px)" data-reactid="11">
                          <tbody data-reactid="12">
                            <tr data-reactid="13">
                              <td data-reactid="14">
                                <span data-reactid="15">Market Cap (intraday)</span><!-- react-text: 16 --> <!-- /react-text --><!-- react-text: 17 --><!-- /react-text --><sup aria-label="Shares outstanding is taken from the most recently filed quarterly or annual report and Market Cap is calculated using shares outstanding." data-reactid="18">5</sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="19">214.12B</td>
                            </tr>
                            <tr data-reactid="20">
                              <td data-reactid="21">
                                <span data-reactid="22">Enterprise Value</span><!-- react-text: 23 --> <!-- /react-text --><!-- react-text: 24 --><!-- /react-text --><sup aria-label="Data derived from multiple sources or calculated by Yahoo Finance." data-reactid="25">3</sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="26">216.26B</td>
                            </tr>
                            <tr data-reactid="27">
                              <td data-reactid="28">
                                <span data-reactid="29">Trailing P/E</span><!-- react-text: 30 --> <!-- /react-text --><!-- react-text: 31 --><!-- /react-text --><sup aria-label="KS_HELP_SUP_undefined" data-reactid="32"></sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="33">21.23</td>
                            </tr>
                            <tr data-reactid="34">
                              <td data-reactid="35">
                                <span data-reactid="36">Forward P/E</span><!-- react-text: 37 --> <!-- /react-text --><!-- react-text: 38 --><!-- /react-text --><sup aria-label="Data provided by Thomson Reuters." data-reactid="39">1</sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="40">16.22</td>
                            </tr>
                            <tr data-reactid="41">
                              <td data-reactid="42">
                                <span data-reactid="43">PEG Ratio (5 yr expected)</span><!-- react-text: 44 --> <!-- /react-text --><!-- react-text: 45 --><!-- /react-text --><sup aria-label="Data provided by Thomson Reuters." data-reactid="46">1</sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="47">0.83</td>
                            </tr>
                            <tr data-reactid="48">
                              <td data-reactid="49">
                                <span data-reactid="50">Price/Sales</span><!-- react-text: 51 --> <!-- /react-text --><!-- react-text: 52 -->(ttm)<!-- /react-text --><sup aria-label="KS_HELP_SUP_undefined" data-reactid="53"></sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="54">2.12</td>
                            </tr>
                            <tr data-reactid="55">
                              <td data-reactid="56">
                                <span data-reactid="57">Price/Book</span><!-- react-text: 58 --> <!-- /react-text --><!-- react-text: 59 -->(mrq)<!-- /react-text --><sup aria-label="KS_HELP_SUP_undefined" data-reactid="60"></sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="61">634.82</td>
                            </tr>
                            <tr data-reactid="62">
                              <td data-reactid="63">
                                <span data-reactid="64">Enterprise Value/Revenue</span><!-- react-text: 65 --> <!-- /react-text --><!-- react-text: 66 --><!-- /react-text --><sup aria-label="Data derived from multiple sources or calculated by Yahoo Finance." data-reactid="67">3</sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="68">2.14</td>
                            </tr>
                            <tr data-reactid="69">
                              <td data-reactid="70">
                                <span data-reactid="71">Enterprise Value/EBITDA</span><!-- react-text: 72 --> <!-- /react-text --><!-- react-text: 73 --><!-- /react-text --><sup aria-label="EBITDA is calculated by Capital IQ using methodology that may differ from that used by a company in its reporting." data-reactid="74">6</sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="75">15.38</td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </div>
                    <h2 class="Pt(20px)" data-reactid="76"><span data-reactid="77">Financial Highlights</span></h2>
                    <div class="Mb(10px) Pend(20px) smartphone_Pend(0px)" data-reactid="78">
                      <div data-reactid="79">
                        <h3 class="Fz(s) Mt(20px)" data-reactid="80"><span data-reactid="81">Fiscal Year</span></h3>
                        <table class="table-qsp-stats Mt(10px)" data-reactid="82">
                          <tbody data-reactid="83">
                            <tr data-reactid="84">
                              <td data-reactid="85">
                                <span data-reactid="86">Fiscal Year Ends</span><!-- react-text: 87 --> <!-- /react-text --><!-- react-text: 88 --><!-- /react-text --><sup aria-label="KS_HELP_SUP_undefined" data-reactid="89"></sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="90">Dec 31, 2018</td>
                            </tr>
                            <tr data-reactid="91">
                              <td data-reactid="92">
                                <span data-reactid="93">Most Recent Quarter</span><!-- react-text: 94 --> <!-- /react-text --><!-- react-text: 95 -->(mrq)<!-- /react-text --><sup aria-label="KS_HELP_SUP_undefined" data-reactid="96"></sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="97">Dec 31, 2018</td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                      <div data-reactid="98">
                        <h3 class="Fz(s) Mt(20px)" data-reactid="99"><span data-reactid="100">Profitability</span></h3>
                        <table class="table-qsp-stats Mt(10px)" data-reactid="101">
                          <tbody data-reactid="102">
                            <tr data-reactid="103">
                              <td data-reactid="104">
                                <span data-reactid="105">Profit Margin</span><!-- react-text: 106 --> <!-- /react-text --><!-- react-text: 107 --><!-- /react-text --><sup aria-label="KS_HELP_SUP_undefined" data-reactid="108"></sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="109">10.34%</td>
                            </tr>
                            <tr data-reactid="110">
                              <td data-reactid="111">
                                <span data-reactid="112">Operating Margin</span><!-- react-text: 113 --> <!-- /react-text --><!-- react-text: 114 -->(ttm)<!-- /react-text --><sup aria-label="KS_HELP_SUP_undefined" data-reactid="115"></sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="116">11.81%</td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                      <div data-reactid="117">
                        <h3 class="Fz(s) Mt(20px)" data-reactid="118"><span data-reactid="119">Management Effectiveness</span></h3>
                        <table class="table-qsp-stats Mt(10px)" data-reactid="120">
                          <tbody data-reactid="121">
                            <tr data-reactid="122">
                              <td data-reactid="123">
                                <span data-reactid="124">Return on Assets</span><!-- react-text: 125 --> <!-- /react-text --><!-- react-text: 126 -->(ttm)<!-- /react-text --><sup aria-label="KS_HELP_SUP_undefined" data-reactid="127"></sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="128">6.50%</td>
                            </tr>
                            <tr data-reactid="129">
                              <td data-reactid="130">
                                <span data-reactid="131">Return on Equity</span><!-- react-text: 132 --> <!-- /react-text --><!-- react-text: 133 -->(ttm)<!-- /react-text --><sup aria-label="KS_HELP_SUP_undefined" data-reactid="134"></sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="135">985.40%</td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                      <div data-reactid="136">
                        <h3 class="Fz(s) Mt(20px)" data-reactid="137"><span data-reactid="138">Income Statement</span></h3>
                        <table class="table-qsp-stats Mt(10px)" data-reactid="139">
                          <tbody data-reactid="140">
                            <tr data-reactid="141">
                              <td data-reactid="142">
                                <span data-reactid="143">Revenue</span><!-- react-text: 144 --> <!-- /react-text --><!-- react-text: 145 -->(ttm)<!-- /react-text --><sup aria-label="KS_HELP_SUP_undefined" data-reactid="146"></sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="147">101.13B</td>
                            </tr>
                            <tr data-reactid="148">
                              <td data-reactid="149">
                                <span data-reactid="150">Revenue Per Share</span><!-- react-text: 151 --> <!-- /react-text --><!-- react-text: 152 -->(ttm)<!-- /react-text --><sup aria-label="KS_HELP_SUP_undefined" data-reactid="153"></sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="154">174.39</td>
                            </tr>
                            <tr data-reactid="155">
                              <td data-reactid="156">
                                <span data-reactid="157">Quarterly Revenue Growth</span><!-- react-text: 158 --> <!-- /react-text --><!-- react-text: 159 -->(yoy)<!-- /react-text --><sup aria-label="KS_HELP_SUP_undefined" data-reactid="160"></sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="161">14.40%</td>
                            </tr>
                            <tr data-reactid="162">
                              <td data-reactid="163">
                                <span data-reactid="164">Gross Profit</span><!-- react-text: 165 --> <!-- /react-text --><!-- react-text: 166 -->(ttm)<!-- /react-text --><sup aria-label="KS_HELP_SUP_undefined" data-reactid="167"></sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="168">19.64B</td>
                            </tr>
                            <tr data-reactid="169">
                              <td data-reactid="170">
                                <span data-reactid="171">EBITDA</span><!-- react-text: 172 --> <!-- /react-text --><!-- react-text: 173 --><!-- /react-text --><sup aria-label="KS_HELP_SUP_undefined" data-reactid="174"></sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="175">14.06B</td>
                            </tr>
                            <tr data-reactid="176">
                              <td data-reactid="177">
                                <span data-reactid="178">Net Income Avi to Common</span><!-- react-text: 179 --> <!-- /react-text --><!-- react-text: 180 -->(ttm)<!-- /react-text --><sup aria-label="KS_HELP_SUP_undefined" data-reactid="181"></sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="182">10.46B</td>
                            </tr>
                            <tr data-reactid="183">
                              <td data-reactid="184">
                                <span data-reactid="185">Diluted EPS</span><!-- react-text: 186 --> <!-- /react-text --><!-- react-text: 187 -->(ttm)<!-- /react-text --><sup aria-label="KS_HELP_SUP_undefined" data-reactid="188"></sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="189">17.85</td>
                            </tr>
                            <tr data-reactid="190">
                              <td data-reactid="191">
                                <span data-reactid="192">Quarterly Earnings Growth</span><!-- react-text: 193 --> <!-- /react-text --><!-- react-text: 194 -->(yoy)<!-- /react-text --><sup aria-label="KS_HELP_SUP_undefined" data-reactid="195"></sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="196">3.10%</td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                      <div data-reactid="197">
                        <h3 class="Fz(s) Mt(20px)" data-reactid="198"><span data-reactid="199">Balance Sheet</span></h3>
                        <table class="table-qsp-stats Mt(10px)" data-reactid="200">
                          <tbody data-reactid="201">
                            <tr data-reactid="202">
                              <td data-reactid="203">
                                <span data-reactid="204">Total Cash</span><!-- react-text: 205 --> <!-- /react-text --><!-- react-text: 206 -->(mrq)<!-- /react-text --><sup aria-label="KS_HELP_SUP_undefined" data-reactid="207"></sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="208">8.56B</td>
                            </tr>
                            <tr data-reactid="209">
                              <td data-reactid="210">
                                <span data-reactid="211">Total Cash Per Share</span><!-- react-text: 212 --> <!-- /react-text --><!-- react-text: 213 -->(mrq)<!-- /react-text --><sup aria-label="KS_HELP_SUP_undefined" data-reactid="214"></sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="215">15.16</td>
                            </tr>
                            <tr data-reactid="216">
                              <td data-reactid="217">
                                <span data-reactid="218">Total Debt</span><!-- react-text: 219 --> <!-- /react-text --><!-- react-text: 220 -->(mrq)<!-- /react-text --><sup aria-label="KS_HELP_SUP_undefined" data-reactid="221"></sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="222">13.85B</td>
                            </tr>
                            <tr data-reactid="223">
                              <td data-reactid="224">
                                <span data-reactid="225">Total Debt/Equity</span><!-- react-text: 226 --> <!-- /react-text --><!-- react-text: 227 -->(mrq)<!-- /react-text --><sup aria-label="KS_HELP_SUP_undefined" data-reactid="228"></sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="229">3,377.32</td>
                            </tr>
                            <tr data-reactid="230">
                              <td data-reactid="231">
                                <span data-reactid="232">Current Ratio</span><!-- react-text: 233 --> <!-- /react-text --><!-- react-text: 234 -->(mrq)<!-- /react-text --><sup aria-label="KS_HELP_SUP_undefined" data-reactid="235"></sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="236">1.08</td>
                            </tr>
                            <tr data-reactid="237">
                              <td data-reactid="238">
                                <span data-reactid="239">Book Value Per Share</span><!-- react-text: 240 --> <!-- /react-text --><!-- react-text: 241 -->(mrq)<!-- /react-text --><sup aria-label="KS_HELP_SUP_undefined" data-reactid="242"></sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="243">0.60</td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                      <div data-reactid="244">
                        <h3 class="Fz(s) Mt(20px)" data-reactid="245"><span data-reactid="246">Cash Flow Statement</span></h3>
                        <table class="table-qsp-stats Mt(10px)" data-reactid="247">
                          <tbody data-reactid="248">
                            <tr data-reactid="249">
                              <td data-reactid="250">
                                <span data-reactid="251">Operating Cash Flow</span><!-- react-text: 252 --> <!-- /react-text --><!-- react-text: 253 -->(ttm)<!-- /react-text --><sup aria-label="KS_HELP_SUP_undefined" data-reactid="254"></sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="255">15.32B</td>
                            </tr>
                            <tr data-reactid="256">
                              <td data-reactid="257">
                                <span data-reactid="258">Levered Free Cash Flow</span><!-- react-text: 259 --> <!-- /react-text --><!-- react-text: 260 -->(ttm)<!-- /react-text --><sup aria-label="KS_HELP_SUP_undefined" data-reactid="261"></sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="262">8.33B</td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                  <div class="Fl(end) W(50%) smartphone_W(100%)" data-reactid="263">
                    <h2 class="Pt(6px) Pstart(20px) smartphone_Pstart(0px)" data-reactid="264"><span data-reactid="265">Trading Information</span></h2>
                    <div class="Pstart(20px) smartphone_Pstart(0px)" data-reactid="266">
                      <div data-reactid="267">
                        <h3 class="Fz(s) Mt(20px)" data-reactid="268"><span data-reactid="269">Stock Price History</span></h3>
                        <table class="table-qsp-stats Mt(10px)" data-reactid="270">
                          <tbody data-reactid="271">
                            <tr data-reactid="272">
                              <td data-reactid="273">
                                <span data-reactid="274">Beta (3Y Monthly)</span><!-- react-text: 275 --> <!-- /react-text --><!-- react-text: 276 --><!-- /react-text --><sup aria-label="KS_HELP_SUP_undefined" data-reactid="277"></sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="278">1.36</td>
                            </tr>
                            <tr data-reactid="279">
                              <td data-reactid="280">
                                <span data-reactid="281">52-Week Change</span><!-- react-text: 282 --> <!-- /react-text --><!-- react-text: 283 --><!-- /react-text --><sup aria-label="Data derived from multiple sources or calculated by Yahoo Finance." data-reactid="284">3</sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="285">12.52%</td>
                            </tr>
                            <tr data-reactid="286">
                              <td data-reactid="287">
                                <span data-reactid="288">S&amp;P500 52-Week Change</span><!-- react-text: 289 --> <!-- /react-text --><!-- react-text: 290 --><!-- /react-text --><sup aria-label="Data derived from multiple sources or calculated by Yahoo Finance." data-reactid="291">3</sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="292">3.52%</td>
                            </tr>
                            <tr data-reactid="293">
                              <td data-reactid="294">
                                <span data-reactid="295">52 Week High</span><!-- react-text: 296 --> <!-- /react-text --><!-- react-text: 297 --><!-- /react-text --><sup aria-label="Data derived from multiple sources or calculated by Yahoo Finance." data-reactid="298">3</sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="299">446.01</td>
                            </tr>
                            <tr data-reactid="300">
                              <td data-reactid="301">
                                <span data-reactid="302">52 Week Low</span><!-- react-text: 303 --> <!-- /react-text --><!-- react-text: 304 --><!-- /react-text --><sup aria-label="Data derived from multiple sources or calculated by Yahoo Finance." data-reactid="305">3</sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="306">292.47</td>
                            </tr>
                            <tr data-reactid="307">
                              <td data-reactid="308">
                                <span data-reactid="309">50-Day Moving Average</span><!-- react-text: 310 --> <!-- /react-text --><!-- react-text: 311 --><!-- /react-text --><sup aria-label="Data derived from multiple sources or calculated by Yahoo Finance." data-reactid="312">3</sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="313">406.30</td>
                            </tr>
                            <tr data-reactid="314">
                              <td data-reactid="315">
                                <span data-reactid="316">200-Day Moving Average</span><!-- react-text: 317 --> <!-- /react-text --><!-- react-text: 318 --><!-- /react-text --><sup aria-label="Data derived from multiple sources or calculated by Yahoo Finance." data-reactid="319">3</sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="320">362.92</td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                      <div data-reactid="321">
                        <h3 class="Fz(s) Mt(20px)" data-reactid="322"><span data-reactid="323">Share Statistics</span></h3>
                        <table class="table-qsp-stats Mt(10px)" data-reactid="324">
                          <tbody data-reactid="325">
                            <tr data-reactid="326">
                              <td data-reactid="327">
                                <span data-reactid="328">Avg Vol (3 month)</span><!-- react-text: 329 --> <!-- /react-text --><!-- react-text: 330 --><!-- /react-text --><sup aria-label="Data derived from multiple sources or calculated by Yahoo Finance." data-reactid="331">3</sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="332">6.35M</td>
                            </tr>
                            <tr data-reactid="333">
                              <td data-reactid="334">
                                <span data-reactid="335">Avg Vol (10 day)</span><!-- react-text: 336 --> <!-- /react-text --><!-- react-text: 337 --><!-- /react-text --><sup aria-label="Data derived from multiple sources or calculated by Yahoo Finance." data-reactid="338">3</sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="339">19.67M</td>
                            </tr>
                            <tr data-reactid="340">
                              <td data-reactid="341">
                                <span data-reactid="342">Shares Outstanding</span><!-- react-text: 343 --> <!-- /react-text --><!-- react-text: 344 --><!-- /react-text --><sup aria-label="Shares outstanding is taken from the most recently filed quarterly or annual report and Market Cap is calculated using shares outstanding." data-reactid="345">5</sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="346">564.99M</td>
                            </tr>
                            <tr data-reactid="347">
                              <td data-reactid="348">
                                <span data-reactid="349">Float</span><!-- react-text: 350 --> <!-- /react-text --><!-- react-text: 351 --><!-- /react-text --><sup aria-label="KS_HELP_SUP_undefined" data-reactid="352"></sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="353">564.57M</td>
                            </tr>
                            <tr data-reactid="354">
                              <td data-reactid="355">
                                <span data-reactid="356">% Held by Insiders</span><!-- react-text: 357 --> <!-- /react-text --><!-- react-text: 358 --><!-- /react-text --><sup aria-label="Data provided by Thomson Reuters." data-reactid="359">1</sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="360">0.07%</td>
                            </tr>
                            <tr data-reactid="361">
                              <td data-reactid="362">
                                <span data-reactid="363">% Held by Institutions</span><!-- react-text: 364 --> <!-- /react-text --><!-- react-text: 365 --><!-- /react-text --><sup aria-label="Data provided by Thomson Reuters." data-reactid="366">1</sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="367">70.52%</td>
                            </tr>
                            <tr data-reactid="368">
                              <td data-reactid="369">
                                <span data-reactid="370">Shares Short (Feb 28, 2019)</span><!-- react-text: 371 --> <!-- /react-text --><!-- react-text: 372 --><!-- /react-text --><sup aria-label="Data provided by Morningstar, Inc." data-reactid="373">4</sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="374">4.87M</td>
                            </tr>
                            <tr data-reactid="375">
                              <td data-reactid="376">
                                <span data-reactid="377">Short Ratio (Feb 28, 2019)</span><!-- react-text: 378 --> <!-- /react-text --><!-- react-text: 379 --><!-- /react-text --><sup aria-label="Data provided by Morningstar, Inc." data-reactid="380">4</sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="381">1.09</td>
                            </tr>
                            <tr data-reactid="382">
                              <td data-reactid="383">
                                <span data-reactid="384">Short % of Float (Feb 28, 2019)</span><!-- react-text: 385 --> <!-- /react-text --><!-- react-text: 386 --><!-- /react-text --><sup aria-label="Data provided by Morningstar, Inc." data-reactid="387">4</sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="388">0.83%</td>
                            </tr>
                            <tr data-reactid="389">
                              <td data-reactid="390">
                                <span data-reactid="391">Short % of Shares Outstanding (Feb 28, 2019)</span><!-- react-text: 392 --> <!-- /react-text --><!-- react-text: 393 --><!-- /react-text --><sup aria-label="Data provided by Morningstar, Inc." data-reactid="394">4</sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="395">0.86%</td>
                            </tr>
                            <tr data-reactid="396">
                              <td data-reactid="397">
                                <span data-reactid="398">Shares Short (prior month Jan 31, 2019)</span><!-- react-text: 399 --> <!-- /react-text --><!-- react-text: 400 --><!-- /react-text --><sup aria-label="Data provided by Morningstar, Inc." data-reactid="401">4</sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="402">5.25M</td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                      <div data-reactid="403">
                        <h3 class="Fz(s) Mt(20px)" data-reactid="404"><span data-reactid="405">Dividends &amp; Splits</span></h3>
                        <table class="table-qsp-stats Mt(10px)" data-reactid="406">
                          <tbody data-reactid="407">
                            <tr data-reactid="408">
                              <td data-reactid="409">
                                <span data-reactid="410">Forward Annual Dividend Rate</span><!-- react-text: 411 --> <!-- /react-text --><!-- react-text: 412 --><!-- /react-text --><sup aria-label="Data provided by Morningstar, Inc." data-reactid="413">4</sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="414">8.22</td>
                            </tr>
                            <tr data-reactid="415">
                              <td data-reactid="416">
                                <span data-reactid="417">Forward Annual Dividend Yield</span><!-- react-text: 418 --> <!-- /react-text --><!-- react-text: 419 --><!-- /react-text --><sup aria-label="Data provided by Morningstar, Inc." data-reactid="420">4</sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="421">2.20%</td>
                            </tr>
                            <tr data-reactid="422">
                              <td data-reactid="423">
                                <span data-reactid="424">Trailing Annual Dividend Rate</span><!-- react-text: 425 --> <!-- /react-text --><!-- react-text: 426 --><!-- /react-text --><sup aria-label="Data derived from multiple sources or calculated by Yahoo Finance." data-reactid="427">3</sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="428">6.84</td>
                            </tr>
                            <tr data-reactid="429">
                              <td data-reactid="430">
                                <span data-reactid="431">Trailing Annual Dividend Yield</span><!-- react-text: 432 --> <!-- /react-text --><!-- react-text: 433 --><!-- /react-text --><sup aria-label="Data derived from multiple sources or calculated by Yahoo Finance." data-reactid="434">3</sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="435">1.83%</td>
                            </tr>
                            <tr data-reactid="436">
                              <td data-reactid="437">
                                <span data-reactid="438">5 Year Average Dividend Yield</span><!-- react-text: 439 --> <!-- /react-text --><!-- react-text: 440 --><!-- /react-text --><sup aria-label="Data provided by Morningstar, Inc." data-reactid="441">4</sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="442">2.29</td>
                            </tr>
                            <tr data-reactid="443">
                              <td data-reactid="444">
                                <span data-reactid="445">Payout Ratio</span><!-- react-text: 446 --> <!-- /react-text --><!-- react-text: 447 --><!-- /react-text --><sup aria-label="Data provided by Morningstar, Inc." data-reactid="448">4</sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="449">38.32%</td>
                            </tr>
                            <tr data-reactid="450">
                              <td data-reactid="451">
                                <span data-reactid="452">Dividend Date</span><!-- react-text: 453 --> <!-- /react-text --><!-- react-text: 454 --><!-- /react-text --><sup aria-label="Data derived from multiple sources or calculated by Yahoo Finance." data-reactid="455">3</sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="456">Mar 1, 2019</td>
                            </tr>
                            <tr data-reactid="457">
                              <td data-reactid="458">
                                <span data-reactid="459">Ex-Dividend Date</span><!-- react-text: 460 --> <!-- /react-text --><!-- react-text: 461 --><!-- /react-text --><sup aria-label="Data provided by Morningstar, Inc." data-reactid="462">4</sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="463">Feb 7, 2019</td>
                            </tr>
                            <tr data-reactid="464">
                              <td data-reactid="465">
                                <span data-reactid="466">Last Split Factor (new per old)</span><!-- react-text: 467 --> <!-- /react-text --><!-- react-text: 468 --><!-- /react-text --><sup aria-label="Data provided by EDGAR Online." data-reactid="469">2</sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="470">1/2</td>
                            </tr>
                            <tr data-reactid="471">
                              <td data-reactid="472">
                                <span data-reactid="473">Last Split Date</span><!-- react-text: 474 --> <!-- /react-text --><!-- react-text: 475 --><!-- /react-text --><sup aria-label="Data derived from multiple sources or calculated by Yahoo Finance." data-reactid="476">3</sup>
                              </td>
                              <td class="Fz(s) Fw(500) Ta(end)" data-reactid="477">Jun 9, 1997</td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                  <div class="Cl(b)" data-reactid="478"></div>
                </div>
              </section>
            </div>
        """
        test_result = yahoo_fin_statistics.extract_info_from_stat_html(test_html)
        fields_expected = ['Market Cap (intraday)', 'Enterprise Value', 'Trailing P/E', 'Forward P/E',
                           'PEG Ratio (5 yr expected)', 'Price/Sales', 'Price/Book', 'Enterprise Value/Revenue',
                           'Enterprise Value/EBITDA', 'Fiscal Year Ends', 'Most Recent Quarter', 'Profit Margin',
                           'Operating Margin', 'Return on Assets', 'Return on Equity', 'Revenue', 'Revenue Per Share',
                           'Quarterly Revenue Growth', 'Gross Profit', 'EBITDA', 'Net Income Avi to Common',
                           'Diluted EPS', 'Quarterly Earnings Growth', 'Total Cash', 'Total Cash Per Share',
                           'Total Debt', 'Total Debt/Equity', 'Current Ratio', 'Book Value Per Share',
                           'Operating Cash Flow', 'Levered Free Cash Flow', 'Beta (3Y Monthly)',
                           '52-Week Change', 'S&P500 52-Week Change', '52 Week High', '52 Week Low',
                           '50-Day Moving Average', '200-Day Moving Average', 'Avg Vol (3 month)',
                           'Avg Vol (10 day)', 'Shares Outstanding', 'Float', '% Held by Insiders',
                           '% Held by Institutions', 'Shares Short (Feb 28, 2019)', 'Short Ratio (Feb 28, 2019)',
                           'Short % of Float (Feb 28, 2019)', 'Short % of Shares Outstanding (Feb 28, 2019)',
                           'Shares Short (prior month Jan 31, 2019)', 'Forward Annual Dividend Rate',
                           'Forward Annual Dividend Yield', 'Trailing Annual Dividend Rate',
                           'Trailing Annual Dividend Yield', '5 Year Average Dividend Yield',
                           'Payout Ratio', 'Dividend Date', 'Ex-Dividend Date', 'Last Split Factor (new per old)',
                           'Last Split Date']
        for field_expected in fields_expected:
            self.assertIn(field_expected, test_result)
        # print(json.dumps(test_result, indent=2))

    def test_convert_to_db_ready(self):
        test_data = {
            "Market Cap (intraday)": 214120000000.0,
            "Enterprise Value": 216260000000.0,
            "Trailing P/E": 21.23,
            "Forward P/E": 16.22,
            "PEG Ratio (5 yr expected)": 0.83,
            "Price/Sales": 2.12,
            "Price/Book": 634.82,
            "Enterprise Value/Revenue": 2.14,
            "Enterprise Value/EBITDA": 15.38,
            "Fiscal Year Ends": "2018-12-31",
            "Most Recent Quarter": "2018-12-31",
            "Profit Margin": 0.1034,
            "Operating Margin": 0.1181,
            "Return on Assets": 0.065,
            "Return on Equity": 9.854,
            "Revenue": 101130000000.0,
            "Revenue Per Share": 174.39,
            "Quarterly Revenue Growth": 0.144,
            "Gross Profit": 19640000000.0,
            "EBITDA": 14060000000.0,
            "Net Income Avi to Common": 10460000000.0,
            "Diluted EPS": 17.85,
            "Quarterly Earnings Growth": 0.031,
            "Total Cash": 8560000000.000001,
            "Total Cash Per Share": 15.16,
            "Total Debt": 13850000000.0,
            "Total Debt/Equity": 3377.32,
            "Current Ratio": 1.08,
            "Book Value Per Share": 0.6,
            "Operating Cash Flow": 15320000000.0,
            "Levered Free Cash Flow": 8330000000.0,
            "Beta (3Y Monthly)": 1.36,
            "52-Week Change": 0.1252,
            "S&P500 52-Week Change": 0.0352,
            "52 Week High": 446.01,
            "52 Week Low": 292.47,
            "50-Day Moving Average": 406.3,
            "200-Day Moving Average": 362.92,
            "Avg Vol (3 month)": 6350000.0,
            "Avg Vol (10 day)": 19670000.0,
            "Shares Outstanding": 564990000.0,
            "Float": 564570000.0,
            "% Held by Insiders": 0.0007,
            "% Held by Institutions": 0.7052,
            "Shares Short (Feb 28, 2019)": 4870000.0,
            "Short Ratio (Feb 28, 2019)": 1.09,
            "Short % of Float (Feb 28, 2019)": 0.0083,
            "Short % of Shares Outstanding (Feb 28, 2019)": 0.0086,
            "Shares Short (prior month Jan 31, 2019)": 5250000.0,
            "Forward Annual Dividend Rate": 8.22,
            "Forward Annual Dividend Yield": 0.022,
            "Trailing Annual Dividend Rate": 6.84,
            "Trailing Annual Dividend Yield": 0.0183,
            "5 Year Average Dividend Yield": 2.29,
            "Payout Ratio": 0.3832,
            "Dividend Date": "2019-03-01",
            "Ex-Dividend Date": "2019-02-07",
            "Last Split Factor (new per old)": 0.5,
            "Last Split Date": "1997-06-09"
        }
        test_record_date = date(2019, 3, 15)
        test_result = yahoo_fin_statistics.convert_to_db_ready(test_data, test_record_date)
        self.assertEqual(test_result["record_date"], "2019-03-15")
        self.assertAlmostEqual(test_result["quarterly_earnings_growth_yoy"], 0.031, 3)

        test_result = yahoo_fin_statistics.convert_to_db_ready(test_data, "2019-03-15")
        self.assertEqual(test_result["record_date"], "2019-03-15")
        self.assertAlmostEqual(test_result["quarterly_earnings_growth_yoy"], 0.031, 3)
        print(json.dumps(test_result, indent=2))


