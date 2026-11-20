| Mutation class | per-principal keys (GUIDE) | shared key (baseline-v0) | no verification (B2) |
|---|---|---|---|
| valid (control) | 0.000 | 0.000 | 0.000 |
| content_edit | 1.000 | 1.000 | 0.000 |
| field_deleted | 1.000 | 1.000 | 0.000 |
| field_added | 1.000 | 1.000 | 0.000 |
| type_changed | 1.000 | 1.000 | 0.000 |
| signature_bitflip | 1.000 | 1.000 | 0.000 |
| content_edit_relinked | 1.000 | 1.000 | 0.000 |
| replay_wrong_parent | 1.000 | 1.000 | 0.000 |
| expired | 1.000 | 1.000 | 0.000 |
| misdelivered | 1.000 | 1.000 | 0.000 |
| sender_spoofed | 1.000 | 0.000 | 0.000 |

Values are rejection rates (n = 500 per cell). For 'valid (control)' the correct value is 0.000 (no false rejections). 'expired' and 'misdelivered' are correctly re-sealed by the legitimate signer, so they test the expiry and receiver checks rather than the signature.
