# Extraction and tone correction

Run repair_extraction.py, then restore_native_tone.py, then queue.py check g08111_v0_s0. The retained old mask erodes foliage and is not used by this corrected extraction. Reviewed direct magenta cleanup preserves the red/orange leaves and real gaps. Native RGB grading preserves alpha. Do not run plain queue process over this final without replaying these corrections.

Tone correction separates red foliage (R > 1.7 G) from brown bark in both native and generated images; this avoids the rejected whole-image green bark cast.
