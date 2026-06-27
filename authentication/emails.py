from django.core.mail import send_mail
from django.conf import settings

def send_register_otp_email(email, otp):
    """
    Sends an informative, styled HTML registration verification email along with a plain text fallback.
    """
    subject = "Verify Your Account - Treats Island"
    
    # Detailed plain text body
    text_content = f"""Hello,

Welcome to Treats Island! Thank you for registering an account with us.

To complete your registration and verify your email address, please use the following One-Time Password (OTP) verification code:

👉 {otp}

Key Details:
- Purpose: New account registration verification
- Valid for: 10 minutes from the time of this email
- Account: {email}

Security Warning:
For your own security, please do not share this verification code with anyone. Treats Island staff will never ask you for this OTP code.

If you did not initiate this registration request, please ignore this email. No further action is required and your email address has not been registered without verification.

Best regards,
The Treats Island Team
"""

    # Richly styled responsive HTML body
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify Your Treats Island Account</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; color: #334155;">
    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f8fafc; padding: 40px 0;">
        <tr>
            <td align="center">
                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); overflow: hidden;">
                    <!-- Header -->
                    <tr>
                        <td align="center" style="background: linear-gradient(135deg, #ff6b81 0%, #ff4757 100%); padding: 35px 20px;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 800; letter-spacing: -0.5px;">Treats Island</h1>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px 30px;">
                            <h2 style="margin-top: 0; margin-bottom: 20px; font-size: 20px; color: #1e293b; font-weight: 700;">Welcome to Treats Island!</h2>
                            <p style="margin: 0 0 24px 0; font-size: 16px; line-height: 24px; color: #475569;">
                                We are thrilled to have you join us. To complete your registration and activate your account, please verify your email address using the One-Time Password (OTP) code below.
                            </p>
                            
                            <!-- OTP Box -->
                            <table border="0" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 30px;">
                                <tr>
                                    <td align="center">
                                        <div style="background-color: #fff5f6; border: 1px solid #ffe3e6; border-radius: 8px; padding: 18px 28px; display: inline-block; font-family: Courier, monospace; letter-spacing: 4px;">
                                            <span style="font-size: 36px; font-weight: 700; color: #ff4757;">{otp}</span>
                                        </div>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Detailed breakdown -->
                            <div style="background-color: #f8fafc; border-left: 4px solid #ff4757; border-radius: 4px; padding: 16px; margin-bottom: 24px;">
                                <h3 style="margin: 0 0 8px 0; font-size: 14px; color: #1e293b; text-transform: uppercase; letter-spacing: 0.5px;">Verification details</h3>
                                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="font-size: 14px; line-height: 20px; color: #475569;">
                                    <tr>
                                        <td style="padding: 2px 0; font-weight: 600; width: 120px; vertical-align: top;">Account Email:</td>
                                        <td style="padding: 2px 0; word-break: break-all;">{email}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 2px 0; font-weight: 600; vertical-align: top;">Validity:</td>
                                        <td style="padding: 2px 0;">10 Minutes</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 2px 0; font-weight: 600; vertical-align: top;">Action:</td>
                                        <td style="padding: 2px 0;">Account Verification</td>
                                    </tr>
                                </table>
                            </div>
                            
                            <p style="margin: 0 0 16px 0; font-size: 13px; line-height: 20px; color: #64748b;">
                                <strong>Security Notice:</strong> Please do not share this OTP with anyone. Treats Island staff will never ask for your passwords or OTP codes.
                            </p>
                            <p style="margin: 0; font-size: 13px; line-height: 20px; color: #64748b;">
                                If you did not make this request, you can safely ignore this email. No account will be activated without verification.
                            </p>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8fafc; padding: 24px 30px; border-top: 1px solid #e2e8f0; text-align: center;">
                            <p style="margin: 0 0 8px 0; font-size: 13px; line-height: 18px; color: #94a3b8;">
                                Sent by the Treats Island Support Team
                            </p>
                            <p style="margin: 0; font-size: 12px; line-height: 16px; color: #cbd5e1;">
                                &copy; 2026 Treats Island. All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    send_mail(
        subject=subject,
        message=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        html_message=html_content,
        fail_silently=False,
    )


def send_forgot_password_otp_email(email, otp):
    """
    Sends an informative, styled HTML password reset verification email along with a plain text fallback.
    """
    subject = "Reset Your Password - Treats Island"
    
    # Detailed plain text body
    text_content = f"""Hello,

We received a request to reset the password for your Treats Island account.

To verify your identity and proceed with setting a new password, please use the following One-Time Password (OTP) verification code:

👉 {otp}

Key Details:
- Purpose: Password reset request
- Valid for: 10 minutes from the time of this email
- Account: {email}

Security Warning:
For your own security, please do not share this verification code with anyone. Treats Island staff will never ask you for this OTP code.

If you did not request a password reset, please ignore this email. Your password will remain secure and unchanged, but you may want to review your account security settings.

Best regards,
The Treats Island Team
"""

    # Richly styled responsive HTML body
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reset Your Treats Island Password</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; color: #334155;">
    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f8fafc; padding: 40px 0;">
        <tr>
            <td align="center">
                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); overflow: hidden;">
                    <!-- Header -->
                    <tr>
                        <td align="center" style="background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); padding: 35px 20px;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 800; letter-spacing: -0.5px;">Treats Island</h1>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px 30px;">
                            <h2 style="margin-top: 0; margin-bottom: 20px; font-size: 20px; color: #1e293b; font-weight: 700;">Password Reset Request</h2>
                            <p style="margin: 0 0 24px 0; font-size: 16px; line-height: 24px; color: #475569;">
                                We received a request to reset the password for your account. If you made this request, please use the One-Time Password (OTP) code below to proceed with setting up a new password.
                            </p>
                            
                            <!-- OTP Box -->
                            <table border="0" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 30px;">
                                <tr>
                                    <td align="center">
                                        <div style="background-color: #f0f7ff; border: 1px solid #dbeafe; border-radius: 8px; padding: 18px 28px; display: inline-block; font-family: Courier, monospace; letter-spacing: 4px;">
                                            <span style="font-size: 36px; font-weight: 700; color: #1d4ed8;">{otp}</span>
                                        </div>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Detailed breakdown -->
                            <div style="background-color: #f8fafc; border-left: 4px solid #1d4ed8; border-radius: 4px; padding: 16px; margin-bottom: 24px;">
                                <h3 style="margin: 0 0 8px 0; font-size: 14px; color: #1e293b; text-transform: uppercase; letter-spacing: 0.5px;">Request details</h3>
                                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="font-size: 14px; line-height: 20px; color: #475569;">
                                    <tr>
                                        <td style="padding: 2px 0; font-weight: 600; width: 120px; vertical-align: top;">Account Email:</td>
                                        <td style="padding: 2px 0; word-break: break-all;">{email}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 2px 0; font-weight: 600; vertical-align: top;">Validity:</td>
                                        <td style="padding: 2px 0;">10 Minutes</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 2px 0; font-weight: 600; vertical-align: top;">Action:</td>
                                        <td style="padding: 2px 0;">Password Reset</td>
                                    </tr>
                                </table>
                            </div>
                            
                            <p style="margin: 0 0 16px 0; font-size: 13px; line-height: 20px; color: #64748b;">
                                <strong>Security Notice:</strong> Please do not share this OTP with anyone. Treats Island staff will never ask for your passwords or OTP codes.
                            </p>
                            <p style="margin: 0; font-size: 13px; line-height: 20px; color: #64748b;">
                                If you did not make this request, you can safely ignore this email. Your password will remain secure and unchanged.
                            </p>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8fafc; padding: 24px 30px; border-top: 1px solid #e2e8f0; text-align: center;">
                            <p style="margin: 0 0 8px 0; font-size: 13px; line-height: 18px; color: #94a3b8;">
                                Sent by the Treats Island Support Team
                            </p>
                            <p style="margin: 0; font-size: 12px; line-height: 16px; color: #cbd5e1;">
                                &copy; 2026 Treats Island. All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    send_mail(
        subject=subject,
        message=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        html_message=html_content,
        fail_silently=False,
    )
