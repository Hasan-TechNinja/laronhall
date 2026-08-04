from django.core.mail import send_mail
from django.conf import settings


def send_welcome_organizer_email(email, organizer_name):
    """
    Sends a welcome email to the Event Organizer upon creating an event.
    """
    subject = "Welcome to Treats Island Candy - Your Virtual Candy Fundraising Journey Begins Now!"
    
    text_content = f"""Dear {organizer_name},

We are thrilled to have you on board for your upcoming fundraising event! As a pioneer in the virtual candy fundraising landscape, we are committed to making this experience as sweet and enjoyable as possible.

Our unique selection of delicious chamoy candies are  sure to delight everyone involved. With our easy-to-navigate platform, we aim to make the process of fundraising as straightforward and effective as possible.

In the coming days, we will share tips and strategies to help you maximize your fundraising potential. Meanwhile, feel free to explore our website and familiarize yourself with our offerings and how the fundraising process works.

Thank you for choosing Treats Island Candy. We look forward to a successful and rewarding partnership!

Best Regards,

GOALS Team
Treats Island GO Virtual Fundraising
"""

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to Treats Island Candy</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; color: #334155;">
    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f8fafc; padding: 40px 0;">
        <tr>
            <td align="center">
                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); overflow: hidden;">
                    <!-- Header -->
                    <tr>
                        <td align="center" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 35px 20px;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 800; letter-spacing: -0.5px;">Treats Island Candy</h1>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px 30px;">
                            <h2 style="margin-top: 0; margin-bottom: 20px; font-size: 20px; color: #1e293b; font-weight: 700;">Dear {organizer_name},</h2>
                            <p style="margin: 0 0 16px 0; font-size: 16px; line-height: 24px; color: #475569;">
                                We are thrilled to have you on board for your upcoming fundraising event! As a pioneer in the virtual candy fundraising landscape, we are committed to making this experience as sweet and enjoyable as possible.
                            </p>
                            <p style="margin: 0 0 16px 0; font-size: 16px; line-height: 24px; color: #475569;">
                                Our unique selection of delicious chamoy candies are  sure to delight everyone involved. With our easy-to-navigate platform, we aim to make the process of fundraising as straightforward and effective as possible.
                            </p>
                            <p style="margin: 0 0 24px 0; font-size: 16px; line-height: 24px; color: #475569;">
                                In the coming days, we will share tips and strategies to help you maximize your fundraising potential. Meanwhile, feel free to explore our website and familiarize yourself with our offerings and how the fundraising process works.
                            </p>
                            <p style="margin: 0 0 24px 0; font-size: 16px; line-height: 24px; color: #475569;">
                                Thank you for choosing Treats Island Candy. We look forward to a successful and rewarding partnership!
                            </p>
                            
                            <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 24px 0;">
                            
                            <p style="margin: 0; font-size: 15px; line-height: 22px; color: #475569; font-weight: 600;">
                                Best Regards,<br>
                                <span style="color: #059669; font-weight: 700;">GOALS Team</span><br>
                                <span style="font-size: 13px; color: #64748b; font-weight: 400;">Treats Island GO Virtual Fundraising</span>
                            </p>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8fafc; padding: 24px 30px; border-top: 1px solid #e2e8f0; text-align: center;">
                            <p style="margin: 0; font-size: 12px; line-height: 16px; color: #cbd5e1;">
                                &copy; 2026 Treats Island Candy. All rights reserved.
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
    try:
        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_content,
            fail_silently=False,
        )
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send welcome email to {email}: {e}")


def send_event_start_soon_email(email, organizer_name):
    """
    Sends a reminder email to the Event Organizer 1 hour before their event starts.
    """
    subject = "Get Ready! Your Virtual Candy Fundraising Event is Starting Soon"
    
    text_content = f"""Dear {organizer_name},

Your virtual candy fundraising event is about to start, and we hope you're as excited as we are! This is a wonderful opportunity to raise funds for your cause while sharing some delicious treats.

In preparation for the event, we recommend sharing the upcoming fundraiser with your community via social media, newsletters, and word of mouth. The more people who know about it, the more successful your event will be.

We're here to support you every step of the way. If you have any questions or need any assistance, don't hesitate to reach out.

Best of luck with your fundraising event!

Best Regards,

GOALS Team
Treats Island GO Virtual Fundraising
"""

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Get Ready! Your Event is Starting Soon</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; color: #334155;">
    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f8fafc; padding: 40px 0;">
        <tr>
            <td align="center">
                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); overflow: hidden;">
                    <!-- Header -->
                    <tr>
                        <td align="center" style="background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); padding: 35px 20px;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 800; letter-spacing: -0.5px;">Treats Island Candy</h1>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px 30px;">
                            <h2 style="margin-top: 0; margin-bottom: 20px; font-size: 20px; color: #1e293b; font-weight: 700;">Dear {organizer_name},</h2>
                            <p style="margin: 0 0 16px 0; font-size: 16px; line-height: 24px; color: #475569;">
                                Your virtual candy fundraising event is about to start, and we hope you're as excited as we are! This is a wonderful opportunity to raise funds for your cause while sharing some delicious treats.
                            </p>
                            <p style="margin: 0 0 16px 0; font-size: 16px; line-height: 24px; color: #475569;">
                                In preparation for the event, we recommend sharing the upcoming fundraiser with your community via social media, newsletters, and word of mouth. The more people who know about it, the more successful your event will be.
                            </p>
                            <p style="margin: 0 0 24px 0; font-size: 16px; line-height: 24px; color: #475569;">
                                We're here to support you every step of the way. If you have any questions or need any assistance, don't hesitate to reach out.
                            </p>
                            <p style="margin: 0 0 24px 0; font-size: 16px; line-height: 24px; color: #475569;">
                                Best of luck with your fundraising event!
                            </p>
                            
                            <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 24px 0;">
                            
                            <p style="margin: 0; font-size: 15px; line-height: 22px; color: #475569; font-weight: 600;">
                                Best Regards,<br>
                                <span style="color: #1d4ed8; font-weight: 700;">GOALS Team</span><br>
                                <span style="font-size: 13px; color: #64748b; font-weight: 400;">Treats Island GO Virtual Fundraising</span>
                            </p>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8fafc; padding: 24px 30px; border-top: 1px solid #e2e8f0; text-align: center;">
                            <p style="margin: 0; font-size: 12px; line-height: 16px; color: #cbd5e1;">
                                &copy; 2026 Treats Island Candy. All rights reserved.
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
    try:
        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_content,
            fail_silently=False,
        )
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send event start soon email to {email}: {e}")


def send_event_twenty_four_hour_reminder_email(email, organizer_name):
    """
    Sends a optimization tips email to the Event Organizer 24 hours after their event starts.
    """
    subject = "Tips to Boost Your Candy Fundraising Success"
    
    text_content = f"""Dear {organizer_name},

We're thrilled to see your enthusiasm for our virtual candy fundraising event! To help you make the most of this opportunity, we wanted to share a few strategies that can amplify your success:

Engage with your community: Share the event on your social media platforms, website, and newsletters and encourage your team members to do the same with their popup stores. Keep your community updated on the progress towards your fundraising goal.

Host virtual events: Consider hosting a virtual kick-off event or a mid-campaign rally. These can be great ways to generate excitement and participation.

Personalize your approach: Encourage your members to share why they're participating in the fundraiser in their popup store messaging. Personal stories can be powerful motivators for potential supporters.

Remember, our team is here to assist you. Don't hesitate to reach out if you have any questions or need help.

Best of luck with your fundraising event!

Best Regards,

GOALS Team
Treats Island GO Virtual Fundraising
"""

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tips to Boost Your Candy Fundraising Success</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; color: #334155;">
    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f8fafc; padding: 40px 0;">
        <tr>
            <td align="center">
                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); overflow: hidden;">
                    <!-- Header -->
                    <tr>
                        <td align="center" style="background: linear-gradient(135deg, #a855f7 0%, #7e22ce 100%); padding: 35px 20px;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 800; letter-spacing: -0.5px;">Treats Island Candy</h1>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px 30px;">
                            <h2 style="margin-top: 0; margin-bottom: 20px; font-size: 20px; color: #1e293b; font-weight: 700;">Dear {organizer_name},</h2>
                            <p style="margin: 0 0 20px 0; font-size: 16px; line-height: 24px; color: #475569;">
                                We're thrilled to see your enthusiasm for our virtual candy fundraising event! To help you make the most of this opportunity, we wanted to share a few strategies that can amplify your success:
                            </p>
                            
                            <!-- Strategies -->
                            <div style="margin-bottom: 20px;">
                                <h3 style="margin: 0 0 6px 0; font-size: 16px; color: #7e22ce; font-weight: 700;">📣 Engage with your community</h3>
                                <p style="margin: 0 0 16px 0; font-size: 15px; line-height: 22px; color: #475569;">
                                    Share the event on your social media platforms, website, and newsletters and encourage your team members to do the same with their popup stores. Keep your community updated on the progress towards your fundraising goal.
                                </p>
                            </div>
                            
                            <div style="margin-bottom: 20px;">
                                <h3 style="margin: 0 0 6px 0; font-size: 16px; color: #7e22ce; font-weight: 700;">🎪 Host virtual events</h3>
                                <p style="margin: 0 0 16px 0; font-size: 15px; line-height: 22px; color: #475569;">
                                    Consider hosting a virtual kick-off event or a mid-campaign rally. These can be great ways to generate excitement and participation.
                                </p>
                            </div>
                            
                            <div style="margin-bottom: 24px;">
                                <h3 style="margin: 0 0 6px 0; font-size: 16px; color: #7e22ce; font-weight: 700;">👤 Personalize your approach</h3>
                                <p style="margin: 0 0 16px 0; font-size: 15px; line-height: 22px; color: #475569;">
                                    Encourage your members to share why they're participating in the fundraiser in their popup store messaging. Personal stories can be powerful motivators for potential supporters.
                                </p>
                            </div>
                            
                            <p style="margin: 0 0 24px 0; font-size: 16px; line-height: 24px; color: #475569;">
                                Remember, our team is here to assist you. Don't hesitate to reach out if you have any questions or need help.
                            </p>
                            <p style="margin: 0 0 24px 0; font-size: 16px; line-height: 24px; color: #475569;">
                                Best of luck with your fundraising event!
                            </p>
                            
                            <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 24px 0;">
                            
                            <p style="margin: 0; font-size: 15px; line-height: 22px; color: #475569; font-weight: 600;">
                                Best Regards,<br>
                                <span style="color: #7e22ce; font-weight: 700;">GOALS Team</span><br>
                                <span style="font-size: 13px; color: #64748b; font-weight: 400;">Treats Island GO Virtual Fundraising</span>
                            </p>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8fafc; padding: 24px 30px; border-top: 1px solid #e2e8f0; text-align: center;">
                            <p style="margin: 0; font-size: 12px; line-height: 16px; color: #cbd5e1;">
                                &copy; 2026 Treats Island Candy. All rights reserved.
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
    try:
        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_content,
            fail_silently=False,
        )
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send 24h reminder email to {email}: {e}")


def send_event_end_thank_you_email(email, organizer_name, organization_name):
    """
    Sends a thank you email to the Event Organizer when an event ends.
    """
    subject = "Thank You for a Successful Virtual Candy Fundraising Event!"
    
    text_content = f"""Dear {organizer_name},

We wanted to take a moment to express our heartfelt thanks for choosing {organization_name} for your recent virtual candy fundraising event. It's been a pleasure working with you, and we hope your experience was as sweet as the candies you've helped distribute!

Your hard work and dedication have made a significant impact on your cause, and we're delighted to have been a part of it.

We'd love to hear about your experience and any feedback you might have. Your insights are invaluable as we continually work to improve our service.

Thank you once again for choosing Treats Island Candy Virtual Fundraiser. We look forward to the possibility of working together again in the future!

Best Regards,

GOALS Team
Treats Island GO Virtual Fundraising
"""

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Thank You for a Successful Event!</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; color: #334155;">
    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f8fafc; padding: 40px 0;">
        <tr>
            <td align="center">
                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); overflow: hidden;">
                    <!-- Header -->
                    <tr>
                        <td align="center" style="background: linear-gradient(135deg, #ec4899 0%, #be185d 100%); padding: 35px 20px;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 800; letter-spacing: -0.5px;">Treats Island Candy</h1>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px 30px;">
                            <h2 style="margin-top: 0; margin-bottom: 20px; font-size: 20px; color: #1e293b; font-weight: 700;">Dear {organizer_name},</h2>
                            <p style="margin: 0 0 16px 0; font-size: 16px; line-height: 24px; color: #475569;">
                                We wanted to take a moment to express our heartfelt thanks for choosing <strong>{organization_name}</strong> for your recent virtual candy fundraising event. It's been a pleasure working with you, and we hope your experience was as sweet as the candies you've helped distribute!
                            </p>
                            <p style="margin: 0 0 16px 0; font-size: 16px; line-height: 24px; color: #475569;">
                                Your hard work and dedication have made a significant impact on your cause, and we're delighted to have been a part of it.
                            </p>
                            <p style="margin: 0 0 24px 0; font-size: 16px; line-height: 24px; color: #475569;">
                                We'd love to hear about your experience and any feedback you might have. Your insights are invaluable as we continually work to improve our service.
                            </p>
                            <p style="margin: 0 0 24px 0; font-size: 16px; line-height: 24px; color: #475569;">
                                Thank you once again for choosing Treats Island Candy Virtual Fundraiser. We look forward to the possibility of working together again in the future!
                            </p>
                            
                            <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 24px 0;">
                            
                            <p style="margin: 0; font-size: 15px; line-height: 22px; color: #475569; font-weight: 600;">
                                Best Regards,<br>
                                <span style="color: #be185d; font-weight: 700;">GOALS Team</span><br>
                                <span style="font-size: 13px; color: #64748b; font-weight: 400;">Treats Island GO Virtual Fundraising</span>
                            </p>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8fafc; padding: 24px 30px; border-top: 1px solid #e2e8f0; text-align: center;">
                            <p style="margin: 0; font-size: 12px; line-height: 16px; color: #cbd5e1;">
                                &copy; 2026 Treats Island Candy. All rights reserved.
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
    try:
        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_content,
            fail_silently=False,
        )
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send end thank you email to {email}: {e}")


def send_new_popup_alert_email(email, organizer_name, member_name, popup_store_name):
    """
    Sends an alert email to the Event Organizer when a participant creates a new pop-up store.
    """
    subject = "Exciting News! A New Pop-Up Store Has Been Created for Your Event"
    
    text_content = f"""Dear {organizer_name},

We're thrilled to share that one of your member participants {member_name}, has set up a pop-up store called {popup_store_name} to begin selling our delicious candies to their supporters! This is a significant step towards reaching your overall goal and every sale from each pop-up store will bring you one step closer to your fundraising target.

We encourage you to support and promote this new store among your community. You can share the news on your social media platforms, newsletters, and other communication channels. The more people who know about it, the more successful your fundraising event will be.

Remember, our team is here to assist you. We look forward to updating you on more progress soon!

Best Regards,

GOALS Team
Treats Island GO Virtual Fundraising
"""

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>New Pop-Up Store Created!</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; color: #334155;">
    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f8fafc; padding: 40px 0;">
        <tr>
            <td align="center">
                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); overflow: hidden;">
                    <!-- Header -->
                    <tr>
                        <td align="center" style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); padding: 35px 20px;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 800; letter-spacing: -0.5px;">Treats Island Candy</h1>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px 30px;">
                            <h2 style="margin-top: 0; margin-bottom: 20px; font-size: 20px; color: #1e293b; font-weight: 700;">Dear {organizer_name},</h2>
                            <p style="margin: 0 0 16px 0; font-size: 16px; line-height: 24px; color: #475569;">
                                We're thrilled to share that one of your member participants <strong>{member_name}</strong>, has set up a pop-up store called <strong>{popup_store_name}</strong> to begin selling our delicious candies to their supporters! This is a significant step towards reaching your overall goal and every sale from each pop-up store will bring you one step closer to your fundraising target.
                            </p>
                            <p style="margin: 0 0 16px 0; font-size: 16px; line-height: 24px; color: #475569;">
                                We encourage you to support and promote this new store among your community. You can share the news on your social media platforms, newsletters, and other communication channels. The more people who know about it, the more successful your fundraising event will be.
                            </p>
                            <p style="margin: 0 0 24px 0; font-size: 16px; line-height: 24px; color: #475569;">
                                Remember, our team is here to assist you. We look forward to updating you on more progress soon!
                            </p>
                            
                            <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 24px 0;">
                            
                            <p style="margin: 0; font-size: 15px; line-height: 22px; color: #475569; font-weight: 600;">
                                Best Regards,<br>
                                <span style="color: #d97706; font-weight: 700;">GOALS Team</span><br>
                                <span style="font-size: 13px; color: #64748b; font-weight: 400;">Treats Island GO Virtual Fundraising</span>
                            </p>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8fafc; padding: 24px 30px; border-top: 1px solid #e2e8f0; text-align: center;">
                            <p style="margin: 0; font-size: 12px; line-height: 16px; color: #cbd5e1;">
                                &copy; 2026 Treats Island Candy. All rights reserved.
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
    try:
        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_content,
            fail_silently=False,
        )
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send new popup alert email to {email}: {e}")


def send_event_banking_details_reminder_email(email, organizer_name):
    """
    Sends a banking details reminder email to the Event Organizer 2 days after campaign starts.
    """
    subject = "Action Required: Please Enter Your Payout Details to Avoid Delay"
    
    text_content = f"""Dear {organizer_name},

We hope your virtual candy fundraising campaign is going wonderfully!

To ensure a smooth and timely distribution of your fundraising profits when your event concludes, please take a moment to enter your banking details in your organizer dashboard. Providing this information now will help avoid any delays with your payout.

If you have already entered this information, please ignore this message. If you need any assistance, our support team is always here to help.

Thank you for choosing Treats Island Candy. We wish you continued success with your fundraiser!

Best Regards,

GOALS Team
Treats Island Candy Virtual Fundraising
"""

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Action Required: Enter Your Payout Details</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; color: #334155;">
    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f8fafc; padding: 40px 0;">
        <tr>
            <td align="center">
                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); overflow: hidden;">
                    <!-- Header -->
                    <tr>
                        <td align="center" style="background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%); padding: 35px 20px;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 800; letter-spacing: -0.5px;">Treats Island Candy</h1>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px 30px;">
                            <h2 style="margin-top: 0; margin-bottom: 20px; font-size: 20px; color: #1e293b; font-weight: 700;">Dear {organizer_name},</h2>
                            <p style="margin: 0 0 16px 0; font-size: 16px; line-height: 24px; color: #475569;">
                                We hope your virtual candy fundraising campaign is going wonderfully!
                            </p>
                            <p style="margin: 0 0 16px 0; font-size: 16px; line-height: 24px; color: #475569;">
                                To ensure a smooth and timely distribution of your fundraising profits when your event concludes, please take a moment to enter your banking details in your organizer dashboard. Providing this information now will help avoid any delays with your payout.
                            </p>
                            <p style="margin: 0 0 24px 0; font-size: 16px; line-height: 24px; color: #475569;">
                                If you have already entered this information, please ignore this message. If you need any assistance, our support team is always here to help.
                            </p>
                            <p style="margin: 0 0 24px 0; font-size: 16px; line-height: 24px; color: #475569;">
                                Thank you for choosing Treats Island Candy. We wish you continued success with your fundraiser!
                            </p>
                            
                            <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 24px 0;">
                            
                            <p style="margin: 0; font-size: 15px; line-height: 22px; color: #475569; font-weight: 600;">
                                Best Regards,<br>
                                <span style="color: #b91c1c; font-weight: 700;">GOALS Team</span><br>
                                <span style="font-size: 13px; color: #64748b; font-weight: 400;">Treats Island Candy Virtual Fundraising</span>
                            </p>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8fafc; padding: 24px 30px; border-top: 1px solid #e2e8f0; text-align: center;">
                            <p style="margin: 0; font-size: 12px; line-height: 16px; color: #cbd5e1;">
                                &copy; 2026 Treats Island Candy. All rights reserved.
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
    try:
        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_content,
            fail_silently=False,
        )
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send banking details reminder email to {email}: {e}")

