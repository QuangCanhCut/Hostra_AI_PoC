# M04 Speech Planner và TTS

Luồng: `AgentResponse / script → SpeechPlanner → SpeechAdmission → TTSService → WAV + AudioArtifact`. Scheduler cuối, lip-sync và compositor thuộc các milestone sau. `AgentResponse` được xem là kết quả từ M03 đáng tin cậy: caller phải bảo đảm nguồn này; contract không tự chứng minh nội dung đã được verifier duyệt.

## An toàn và phê duyệt

`SpeechPlanner.from_response` bảo toàn nội dung `answered` và `clarification_needed`. `blocked` chỉ được dùng script `safe_fallback` với `approval.status=approved`, `approved_by` và `approved_at` có múi giờ. Product intro phải đúng active SKU. Các script có `use_when` hoặc `evidence_refs` cần callback kiểm tra điều kiện và bằng chứng trước khi được chấp nhận. Callback là trách nhiệm của service/operator, không được luôn trả true trong production.

Thư viện `shared_data/inputs/approved_product_scripts.json` hiện ở trạng thái chờ review; không phát script pending. Nhóm cần đối chiếu catalog, điều kiện, nội dung và quyền, sau đó người có thẩm quyền mới cập nhật trạng thái và thông tin phê duyệt. Test chỉ dùng fixture approved riêng.

`SpeechAdmission` chỉ nhận turn do cùng instance planner tạo, từ chối trùng ID và cho phép tiêu thụ một lần. Mức ưu tiên fallback → reply → intro; FIFO khi cùng mức. Đây là admission trong một tiến trình, không phải hàng đợi bền vững hay security boundary chống code chạy cùng tiến trình. Sau lỗi TTS cần lập turn mới và admit lại một cách chủ động.

## Audio và cấu hình

Các trường `tts` trong `configs/app.yaml` quy định provider, model, voice, tốc độ, timeout, sample rate và `live_api_opt_in`. Mặc định opt-in là false. `MockTTSProvider` tạo khoảng lặng chỉ để test, không phải giọng nói. `TTSService` ghi WAV PCM signed 16-bit mono, mặc định 16 kHz; hỗ trợ chuyển từ WAV PCM 16-bit mono/stereo qua nội suy tuyến tính và kiểm tra lại file. Không hỗ trợ WAV PCM 8/24/32-bit hoặc codec nén. Bộ chuyển đổi tuyến tính chưa được đánh giá chất lượng âm thanh/khử aliasing và cần benchmark trước sử dụng thật.

`write_run_metadata` chỉ ghi `speech_turns.json` và `audio_artifacts.json` khi gọi tường minh, xác minh lại WAV và liên kết; không ghi đè. Các file WAV được tạo dưới `shared_data/runs/<run_id>/step1_agent_audio/audio/`. Audio ID là tên file; duration đo từ frame count. Không chạy scheduler hoặc tự tạo manifest phiên.

## OpenAI và bàn giao

`OpenAITTSProvider` gọi Speech API khi `provider=openai` và `live_api_opt_in=true`; request có thể phát sinh phí. Chỉ gửi text lượt nói, không gửi viewer ID. Không tự đọc `.env`, retry được tắt. Cần bật opt-in có chủ đích và có credential trước smoke test; test mặc định dùng client giả, không gọi mạng.

Theo [tài liệu TTS OpenAI](https://developers.openai.com/api/docs/guides/text-to-speech), `gpt-4o-mini-tts` và Speech API model cũ dự kiến ngừng ngày 06/01/2027. Adapter này là tạm thời; migration tới `gpt-realtime-2.1-mini` cần tích hợp Realtime API riêng, không chỉ đổi tên model. Phải thông báo cho người nghe đây là giọng AI và đánh giá giọng tiếng Việt bằng nghe thử.

Part 2 chưa có worker thực tế trong repository để xác nhận 16 kHz. Bên nhận phải xác nhận sample rate, format, duration và yêu cầu phiên bản model lip-sync cụ thể. Final Scheduler quyết định timeline dựa trên duration WAV đo được. Không giả định smoke API hoặc chất lượng giọng đã được xác thực từ mock tests.
