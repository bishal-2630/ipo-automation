package com.example.ipo_automation

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.telephony.SmsMessage
import android.util.Log
import org.json.JSONArray
import org.json.JSONObject
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL
import java.text.SimpleDateFormat
import java.util.*
import kotlin.concurrent.thread

class NativeOtpReceiver : BroadcastReceiver() {
    private val TAG = "NativeOtpReceiver"

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == "android.provider.Telephony.SMS_RECEIVED") {
            val bundle = intent.extras
            if (bundle != null) {
                val pdus = bundle.get("pdus") as Array<*>
                for (pdu in pdus) {
                    val message = SmsMessage.createFromPdu(pdu as ByteArray)
                    val body = message.displayMessageBody
                    val address = message.displayOriginatingAddress

                    handleSms(context, address, body)
                }
            }
        }
    }

    private fun handleSms(context: Context, address: String, body: String) {
        val otpRegex = Regex("\\b\\d{6}\\b")
        val otpMatch = otpRegex.find(body)
        
        val isBankingSms = body.contains(Regex("OTP|code|verification|passcode|Pin|Transaction|auth|Confirm|Verify|Applied|MeroShare|CASBA", RegexOption.IGNORE_CASE)) ||
                address.contains(Regex("NIC|Nabil|NMB|PRABHU|Siddhartha|Global|Sanima|Kumari|Citizens|Laxmi|Sunrise|Agriculture|AD-|Nepal|MeShare|620|320", RegexOption.IGNORE_CASE))

        if (otpMatch != null && isBankingSms) {
            val otp = otpMatch.value
            logEvent(context, address, "NATIVE_MATCH: OTP Detected [$otp]")
            relayOtp(context, address, otp)
        }
    }

    private fun relayOtp(context: Context, address: String, otp: String) {
        thread {
            try {
                val prefs = context.getSharedPreferences("FlutterSharedPreferences", Context.MODE_PRIVATE)
                val token = prefs.getString("flutter.token", null)
                
                if (token == null) {
                    logEvent(context, address, "NATIVE_FAIL: No Token found")
                    return@thread
                }

                val url = URL("https://ipoautomation.vercel.app/api/bank-otps/")
                val conn = url.openConnection() as HttpURLConnection
                conn.requestMethod = "POST"
                conn.setRequestProperty("Content-Type", "application/json")
                conn.setRequestProperty("Authorization", "Token $token")
                conn.doOutput = true

                val jsonBody = JSONObject()
                jsonBody.put("otp_code", otp)

                val writer = OutputStreamWriter(conn.outputStream)
                writer.write(jsonBody.toString())
                writer.flush()
                writer.close()

                val responseCode = conn.responseCode
                if (responseCode == 201) {
                    logEvent(context, address, "NATIVE_SUCCESS: Relayed $otp")
                } else {
                    logEvent(context, address, "NATIVE_API_ERROR: HTTP $responseCode")
                }
                conn.disconnect()
            } catch (e: Exception) {
                logEvent(context, address, "NATIVE_CRASH: ${e.message}")
            }
        }
    }

    private fun logEvent(context: Context, address: String, status: String) {
        try {
            val prefs = context.getSharedPreferences("FlutterSharedPreferences", Context.MODE_PRIVATE)
            val currentLogs = prefs.getStringSet("flutter.relay_debug_logs", mutableSetOf<String>()) ?: mutableSetOf<String>()
            
            // Convert to a List to handle ordering (StringSet has no fixed order)
            // Note: We'll store them back as a Set, usually Flutter reads them and sorts them or we just append.
            // Since we want the latest at the top in the UI, we'll prefix them with timestamps.
            
            val sdf = SimpleDateFormat("HH:mm:ss", Locale.getDefault())
            val now = sdf.format(Date())
            val newEntry = "[$now] $address: $status"
            
            val updatedLogs = mutableSetOf<String>()
            updatedLogs.add(newEntry)
            
            // Add existing logs, up to a limit
            val existingList = currentLogs.toList().sorted().reversed() // Rough sort to keep some order
            for (i in 0 until Math.min(existingList.size, 15)) {
                updatedLogs.add(existingList[i])
            }
            
            prefs.edit().putStringSet("flutter.relay_debug_logs", updatedLogs).apply()
        } catch (e: Exception) {
            Log.e(TAG, "Failed to log native event: ${e.message}")
        }
    }
}
