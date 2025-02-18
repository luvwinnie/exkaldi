def configure(name):
	if name == 'compute_mfcc':
		return {"--allow-downsample":["false",str],
				"--allow-upsample":["false",str],
				"--blackman-coeff":[0.42,float],
				"--cepstral-lifter":[22,int],
				"--channel":[-1,int],
				"--debug-mel":["false",str],
				"--dither":[1,int],
				"--energy-floor":[0,int],
				"--frame-length":[25,int],
				"--frame-shift":[10,int],
				"--high-freq":[0,int],
				"--htk-compat":["false",str],
				"--low-freq":[20,int],
				"--max-feature-vectors":[-1,int],
				"--min-duration":[0,int],
				"--num-ceps":[13,int],
				"--num-mel-bins":[23,int],
				"--output-format":["kaldi",str],
				"--preemphasis-coefficient":[0.97,float],
				"--raw-energy":["true",str],
				"--remove-dc-offset":["true",str],
				"--round-to-power-of-two":["true",str],
				"--sample-frequency":[16000,int],
				"--snip-edges":["false",str],
				"--subtract-mean":["false",str],
				"--use-energy":["true",str],
				"--utt2spk":["",str],
				"--vtln-high":[-500,int],
				"--vtln-low":[100,int],
				"--vtln-map":["",str],
				"--vtln-warp":[1,int],
				"--window-type":["povey",str],
				"--write-utt2dur":["",str]
			}
	elif name == 'compute_fbank':
		return {"--allow-downsample":["false",str],
				"--allow-upsample":["false",str],
				"--blackman-coeff":[0.42,float],
				"--channel":[-1,int],
				"--debug-mel":["false",str],
				"--dither":[1,int],
				"--energy-floor":[0,int],
				"--frame-length":[25,int],
				"--frame-shift":[10,int],
				"--high-freq":[0,int],
				"--htk-compat":["false",str],
				"--low-freq":[20,int],
				"--max-feature-vectors":[-1,int],
				"--min-duration":[0,int],
				"--num-mel-bins":[23,int],
				"--output-format":["kaldi",str],
				"--preemphasis-coefficient":[0.97,float],
				"--raw-energy":["true",str],
				"--remove-dc-offset":["true",str],
				"--round-to-power-of-two":["true",str],
				"--sample-frequency":[16000,int],
				"--snip-edges":["false",str],
				"--subtract-mean":["false",str],
				"--use-energy":["true",str],
				"--use-log-fbank":["true",str],
				"--use-power":["true",str],				
				"--utt2spk":["",str],
				"--vtln-high":[-500,int],
				"--vtln-low":[100,int],
				"--vtln-map":["",str],
				"--vtln-warp":[1,int],
				"--window-type":["povey",str],
				"--write-utt2dur":["",str]
			}    
	elif name == 'compute_plp':
		return {"--allow-downsample":["false",str],
				"--allow-upsample":["false",str],
				"--blackman-coeff":[0.42,float],
				"--cepstral-lifter":[22,int],
				"--cepstral-scale":[1,int],
				"--channel":[-1,int],
				"--compress-factor":[0.33333,float],
				"--debug-mel":['false',float],
				"--dither":[1,int],
				"--energy-floor":[0,int],
				"--frame-length":[25,int],
				"--frame-shift":[10,int],
				"--high-freq":[0,int],
				"--htk-compat":["false",str],
				"--low-freq":[20,int],
				"--lpc-order":[12,int],
				"--max-feature-vectors":[-1,int],
				"--min-duration":[0,int],
				"--num-ceps":[13,int],
				"--num-mel-bins":[23,int],
				"--output-format":["kaldi",str],
				"--preemphasis-coefficient":[0.97,float],
				"--raw-energy":["true",str],
				"--remove-dc-offset":["true",str],
				"--round-to-power-of-two":["true",str],
				"--sample-frequency":[16000,int],
				"--snip-edges":["false",str],
				"--subtract-mean":["false",str],
				"--use-energy":["true",str],			
				"--utt2spk":["",str],
				"--vtln-high":[-500,int],
				"--vtln-low":[100,int],
				"--vtln-map":["",str],
				"--vtln-warp":[1,int],
				"--window-type":["povey",str],
				"--write-utt2dur":["",str]
			} 
	elif name == 'compute_spectrogram':
		return {"--allow-downsample":["false",str],
				"--allow-upsample":["false",str],
				"--blackman-coeff":[0.42,float],
				"--channel":[-1,int],
				"--dither":[1,int],
				"--energy-floor":[0,int],
				"--frame-length":[25,int],
				"--frame-shift":[10,int],
				"--max-feature-vectors":[-1,int],
				"--min-duration":[0,int],
				"--output-format":["kaldi",str],
				"--preemphasis-coefficient":[0.97,float],
				"--raw-energy":["true",str],
				"--remove-dc-offset":["true",str],
				"--round-to-power-of-two":["true",str],
				"--sample-frequency":[16000,int],
				"--snip-edges":["false",str],
				"--subtract-mean":["false",str],
				"--window-type":["povey",str],
				"--write-utt2dur":["",str]
			} 
	elif name == 'decode_lattice':
		return {"--acoustic-scale":[0.1,float],
				"--allow-partial":["false",str],
				"--beam":[13,int],
				"--beam-delta":[0.5,float],
				"--delta":[0.000976562,float],
				"--determinize-lattice":["true",str],
				"--hash-ratio":[2,int],
				"--lattice-beam":[8,int],
				"--max-active":[7000,int],
				"--max-mem":[50000000,int],
				"--min-active":[200,int],
				"--minimize":["false",str],
				"--phone-determinize":["true",str],
				"--prune-interval":[25,int],
				"--word-determinize":["true",str],
				"--word-symbol-table":["",str]
			} 
	else:
		return None

