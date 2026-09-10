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


def send_order_confirmation_email(email, customer_name, orders):
    """
    Sends an order confirmation email to the customer.
    """
    subject = "Order Confirmation - Treats Island Candy"
    
    order_items_text = ""
    order_items_html = ""
    total = 0.0
    
    for order in orders:
        price = 0.0
        try:
            price = float(order.product.price)
        except:
            pass
        item_total = price * order.quantity
        total += item_total
        
        order_items_text += f"- {order.product.name} (x{order.quantity}) - ${item_total:.2f}\n"
        order_items_html += f"""
        <tr>
            <td style="padding: 12px 0; border-bottom: 1px solid #e2e8f0; color: #475569;">
                {order.product.name} (x{order.quantity})
            </td>
            <td style="padding: 12px 0; border-bottom: 1px solid #e2e8f0; text-align: right; color: #1e293b; font-weight: 600;">
                ${item_total:.2f}
            </td>
        </tr>
        """
        
    shipping_charge = 0.0
    for order in orders:
        try:
            if order.delivery_charge:
                shipping_charge += float(order.delivery_charge)
        except (ValueError, TypeError):
            pass

    total += shipping_charge

    order_items_text += f"- Shipping - ${shipping_charge:.2f}\n"
    order_items_html += f"""
        <tr>
            <td style="padding: 12px 0; border-bottom: 1px solid #e2e8f0; color: #475569;">
                Standard Shipping
            </td>
            <td style="padding: 12px 0; border-bottom: 1px solid #e2e8f0; text-align: right; color: #1e293b; font-weight: 600;">
                ${shipping_charge:.2f}
            </td>
        </tr>
    """
    
    text_content = f"""Dear {customer_name},

Thank you for your order! Your purchase directly helps our fundraising efforts, and we are so grateful for your support.

Here are your order details:
{order_items_text}
Total Paid: ${total:.2f}

We are currently preparing your delicious treats. You will receive another notification once your order ships.

If you have any questions, please reply to this email.

Best Regards,
Treats Island Candy Team
"""

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Order Confirmation</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; color: #334155;">
    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="padding: 40px 0;">
        <tr>
            <td align="center">
                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                    <tr>
                        <td align="center" style="background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%); padding: 35px 20px;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 800;">Order Confirmation</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 40px 30px;">
                            <h2 style="margin-top: 0; margin-bottom: 20px; font-size: 20px; color: #1e293b;">Hi {customer_name},</h2>
                            <p style="margin: 0 0 16px 0; font-size: 16px; line-height: 24px; color: #475569;">
                                Thank you for your order! Your purchase directly helps our fundraising efforts, and we are so grateful for your support.
                            </p>
                            
                            <div style="background-color: #f8fafc; border-radius: 8px; padding: 20px; margin: 24px 0;">
                                <h3 style="margin: 0 0 16px 0; font-size: 16px; color: #1e293b;">Order Summary</h3>
                                <table width="100%" cellpadding="0" cellspacing="0" style="font-size: 15px;">
                                    {order_items_html}
                                    <tr>
                                        <td style="padding-top: 16px; font-weight: 600; color: #1e293b;">Total Paid</td>
                                        <td style="padding-top: 16px; text-align: right; font-weight: 700; color: #2563eb; font-size: 18px;">${total:.2f}</td>
                                    </tr>
                                </table>
                            </div>
                            
                            <p style="margin: 0 0 24px 0; font-size: 16px; line-height: 24px; color: #475569;">
                                We are currently preparing your delicious treats. We will let you know as soon as your order ships.
                            </p>
                            
                            <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 24px 0;">
                            
                            <p style="margin: 0; font-size: 15px; color: #475569; font-weight: 600;">
                                Best Regards,<br>
                                <span style="color: #1e40af;">Treats Island Candy Team</span>
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
        from django.core.mail import send_mail
        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_content,
            fail_silently=False,
        )
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send order confirmation to {email}: {e}")


def send_event_created_admin_email(event):
    """
    Sends a notification email to the Admin when a new event is created.
    """
    admin_email = getattr(settings, 'ADMIN_EMAIL', 'hasantechninja@gmail.com')
    subject = f"New Event Created: {event.name or event.code}"
    
    organizer_name = (event.creator.full_name or event.creator.phone) if event.creator else "Unknown"
    organizer_email = event.creator.email if event.creator else "-"
    organizer_phone = event.creator.phone if event.creator else "-"
    org_type = event.type.name if event.type else "-"
    start_date_str = event.start_date.strftime("%B %d, %Y, %I:%M %p") if event.start_date else "-"
    end_date_str = event.end_date.strftime("%B %d, %Y, %I:%M %p") if event.end_date else "-"
    duration_str = f"{event.duration} Days" if event.duration else "-"
    
    text_content = f"""Hello Admin,

A new event has been created on Treats Island!

Event Details:
- Name of Organization: {event.name or '-'}
- Organization Type: {org_type}
- Event Code: {event.code or '-'}
- Duration: {duration_str}
- Start Date: {start_date_str}
- End Date: {end_date_str}

Organizer Details:
- Name: {organizer_name}
- Email: {organizer_email}
- Phone: {organizer_phone}

Best Regards,
Treats Island GO Virtual Fundraising
"""
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>New Event Created</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #334155;">
    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f8fafc; padding: 40px 0;">
        <tr>
            <td align="center">
                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); overflow: hidden;">
                    <tr>
                        <td align="center" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 30px 20px;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 800;">New Event Created</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 30px;">
                            <h2 style="margin-top: 0; margin-bottom: 16px; font-size: 18px; color: #1e293b;">Hello Admin,</h2>
                            <p style="margin: 0 0 20px 0; font-size: 15px; line-height: 22px; color: #475569;">
                                A new fundraising event has been created on the platform.
                            </p>
                            
                            <div style="background-color: #f8fafc; border-radius: 8px; padding: 20px; margin-bottom: 24px; border: 1px solid #e2e8f0;">
                                <h3 style="margin: 0 0 12px 0; font-size: 16px; color: #059669; font-weight: 700;">Event Information</h3>
                                <table width="100%" cellpadding="6" cellspacing="0" style="font-size: 14px; color: #334155;">
                                    <tr>
                                        <td style="font-weight: 600; width: 40%;">Name of Organization:</td>
                                        <td>{event.name or '-'}</td>
                                    </tr>
                                    <tr>
                                        <td style="font-weight: 600;">Organization Type:</td>
                                        <td>{org_type}</td>
                                    </tr>
                                    <tr>
                                        <td style="font-weight: 600;">Event Code:</td>
                                        <td><strong>{event.code or '-'}</strong></td>
                                    </tr>
                                    <tr>
                                        <td style="font-weight: 600;">Duration:</td>
                                        <td>{duration_str}</td>
                                    </tr>
                                    <tr>
                                        <td style="font-weight: 600;">Start Date:</td>
                                        <td>{start_date_str}</td>
                                    </tr>
                                    <tr>
                                        <td style="font-weight: 600;">End Date:</td>
                                        <td>{end_date_str}</td>
                                    </tr>
                                </table>
                            </div>

                            <div style="background-color: #f8fafc; border-radius: 8px; padding: 20px; margin-bottom: 24px; border: 1px solid #e2e8f0;">
                                <h3 style="margin: 0 0 12px 0; font-size: 16px; color: #059669; font-weight: 700;">Organizer Details</h3>
                                <table width="100%" cellpadding="6" cellspacing="0" style="font-size: 14px; color: #334155;">
                                    <tr>
                                        <td style="font-weight: 600; width: 40%;">Name:</td>
                                        <td>{organizer_name}</td>
                                    </tr>
                                    <tr>
                                        <td style="font-weight: 600;">Email:</td>
                                        <td>{organizer_email}</td>
                                    </tr>
                                    <tr>
                                        <td style="font-weight: 600;">Phone:</td>
                                        <td>{organizer_phone}</td>
                                    </tr>
                                </table>
                            </div>
                            
                            <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 24px 0;">
                            
                            <p style="margin: 0; font-size: 14px; line-height: 20px; color: #64748b;">
                                Best Regards,<br>
                                <strong style="color: #059669;">Treats Island GO Virtual Fundraising</strong>
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
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'Treats Island <hasantechninja@gmail.com>')
        send_mail(
            subject=subject,
            message=text_content,
            from_email=from_email,
            recipient_list=[admin_email],
            html_message=html_content,
            fail_silently=False,
        )
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send event created admin email: {e}")


def send_popup_store_created_admin_email(fundraiser):
    """
    Sends a notification email to the Admin when a new pop-up store is created.
    """
    admin_email = getattr(settings, 'ADMIN_EMAIL', 'hasantechninja@gmail.com')
    store_name = fundraiser.name or f"Store #{fundraiser.id}"
    subject = f"New Pop-Up Store Created: {store_name}"

    member_name = (fundraiser.user.full_name or fundraiser.user.phone) if fundraiser.user else "Unknown"
    member_email = fundraiser.user.email if fundraiser.user else "-"
    member_phone = fundraiser.user.phone if fundraiser.user else "-"
    
    event = fundraiser.event
    event_name = event.name or event.code if event else "-"
    event_code = event.code if event else "-"
    organizer_name = (event.creator.full_name or event.creator.phone) if event and event.creator else "-"
    organizer_email = event.creator.email if event and event.creator else "-"
    goal_str = f"${fundraiser.goal:,.2f}" if fundraiser.goal else "$0.00"
    store_url = f"https://treatsislandgo.com/store/{fundraiser.id}"

    text_content = f"""Hello Admin,

A new pop-up store '{store_name}' has been created!

Store Details:
- Store Name: {store_name}
- Store Goal: {goal_str}
- Store URL: {store_url}

Store Creator (Member):
- Name: {member_name}
- Email: {member_email}
- Phone: {member_phone}

Event Details:
- Event: {event_name}
- Event Code: {event_code}
- Organizer: {organizer_name} ({organizer_email})

Best Regards,
Treats Island GO Virtual Fundraising
"""
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>New Pop-Up Store Created</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #334155;">
    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f8fafc; padding: 40px 0;">
        <tr>
            <td align="center">
                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); overflow: hidden;">
                    <tr>
                        <td align="center" style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); padding: 30px 20px;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 800;">New Pop-Up Store Created</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 30px;">
                            <h2 style="margin-top: 0; margin-bottom: 16px; font-size: 18px; color: #1e293b;">Hello Admin,</h2>
                            <p style="margin: 0 0 20px 0; font-size: 15px; line-height: 22px; color: #475569;">
                                A new pop-up store <strong>{store_name}</strong> has been created.
                            </p>
                            
                            <div style="background-color: #f8fafc; border-radius: 8px; padding: 20px; margin-bottom: 24px; border: 1px solid #e2e8f0;">
                                <h3 style="margin: 0 0 12px 0; font-size: 16px; color: #d97706; font-weight: 700;">Store Information</h3>
                                <table width="100%" cellpadding="6" cellspacing="0" style="font-size: 14px; color: #334155;">
                                    <tr>
                                        <td style="font-weight: 600; width: 40%;">Store Name:</td>
                                        <td>{store_name}</td>
                                    </tr>
                                    <tr>
                                        <td style="font-weight: 600;">Fundraising Goal:</td>
                                        <td>{goal_str}</td>
                                    </tr>
                                    <tr>
                                        <td style="font-weight: 600;">Store Link:</td>
                                        <td><a href="{store_url}" style="color: #d97706;">{store_url}</a></td>
                                    </tr>
                                </table>
                            </div>

                            <div style="background-color: #f8fafc; border-radius: 8px; padding: 20px; margin-bottom: 24px; border: 1px solid #e2e8f0;">
                                <h3 style="margin: 0 0 12px 0; font-size: 16px; color: #d97706; font-weight: 700;">Store Creator (Participant)</h3>
                                <table width="100%" cellpadding="6" cellspacing="0" style="font-size: 14px; color: #334155;">
                                    <tr>
                                        <td style="font-weight: 600; width: 40%;">Name:</td>
                                        <td>{member_name}</td>
                                    </tr>
                                    <tr>
                                        <td style="font-weight: 600;">Email:</td>
                                        <td>{member_email}</td>
                                    </tr>
                                    <tr>
                                        <td style="font-weight: 600;">Phone:</td>
                                        <td>{member_phone}</td>
                                    </tr>
                                </table>
                            </div>

                            <div style="background-color: #f8fafc; border-radius: 8px; padding: 20px; margin-bottom: 24px; border: 1px solid #e2e8f0;">
                                <h3 style="margin: 0 0 12px 0; font-size: 16px; color: #d97706; font-weight: 700;">Associated Event</h3>
                                <table width="100%" cellpadding="6" cellspacing="0" style="font-size: 14px; color: #334155;">
                                    <tr>
                                        <td style="font-weight: 600; width: 40%;">Event Name:</td>
                                        <td>{event_name}</td>
                                    </tr>
                                    <tr>
                                        <td style="font-weight: 600;">Event Code:</td>
                                        <td>{event_code}</td>
                                    </tr>
                                    <tr>
                                        <td style="font-weight: 600;">Organizer:</td>
                                        <td>{organizer_name} ({organizer_email})</td>
                                    </tr>
                                </table>
                            </div>
                            
                            <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 24px 0;">
                            
                            <p style="margin: 0; font-size: 14px; line-height: 20px; color: #64748b;">
                                Best Regards,<br>
                                <strong style="color: #d97706;">Treats Island GO Virtual Fundraising</strong>
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
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'Treats Island <hasantechninja@gmail.com>')
        send_mail(
            subject=subject,
            message=text_content,
            from_email=from_email,
            recipient_list=[admin_email],
            html_message=html_content,
            fail_silently=False,
        )
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send popup store created admin email: {e}")


def send_popup_store_created_member_email(email, member_name, popup_store_name, event_name, store_url):
    """
    Sends a confirmation email to the participant/member when their pop-up store is created.
    """
    subject = f"Your Pop-Up Store '{popup_store_name}' is Ready! - Treats Island Candy"

    text_content = f"""Dear {member_name},

Congratulations! Your pop-up store '{popup_store_name}' for event '{event_name}' is now live and ready to take orders!

Here is your store link to share with supporters, friends, and family:
{store_url}

Tips for success:
- Share your link on social media, text messages, and email.
- Ask family and friends to spread the word.
- Every order helps your team reach its fundraising goal!

Thank you for participating and supporting {event_name}!

Best Regards,
Treats Island GO Virtual Fundraising
"""
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your Pop-Up Store is Live!</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #334155;">
    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f8fafc; padding: 40px 0;">
        <tr>
            <td align="center">
                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); overflow: hidden;">
                    <tr>
                        <td align="center" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 35px 20px;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 26px; font-weight: 800;">Your Pop-Up Store is Live!</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 35px 30px;">
                            <h2 style="margin-top: 0; margin-bottom: 16px; font-size: 20px; color: #1e293b;">Dear {member_name},</h2>
                            <p style="margin: 0 0 16px 0; font-size: 16px; line-height: 24px; color: #475569;">
                                Congratulations! Your pop-up store <strong>{popup_store_name}</strong> for event <strong>{event_name}</strong> is now live and ready to take orders!
                            </p>
                            
                            <div style="background-color: #ecfdf5; border-radius: 8px; padding: 20px; margin: 24px 0; border: 1px solid #a7f3d0; text-align: center;">
                                <p style="margin: 0 0 10px 0; font-size: 14px; color: #065f46; font-weight: 600;">Your Pop-Up Store Link:</p>
                                <a href="{store_url}" style="display: inline-block; padding: 12px 24px; background-color: #059669; color: #ffffff; text-decoration: none; border-radius: 6px; font-weight: 700; font-size: 15px;">Visit Your Store</a>
                                <p style="margin: 10px 0 0 0; font-size: 13px; color: #047857; word-break: break-all;">{store_url}</p>
                            </div>
                            
                            <h3 style="margin: 20px 0 10px 0; font-size: 16px; color: #1e293b;">Tips for Success:</h3>
                            <ul style="margin: 0 0 20px 0; padding-left: 20px; font-size: 15px; line-height: 22px; color: #475569;">
                                <li>Share your link via social media, text messages, and email.</li>
                                <li>Ask family and friends to share your store with their network.</li>
                                <li>Every delicious candy order brings your team closer to its goal!</li>
                            </ul>
                            
                            <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 24px 0;">
                            
                            <p style="margin: 0; font-size: 15px; line-height: 22px; color: #475569;">
                                Best Regards,<br>
                                <strong style="color: #059669;">Treats Island GO Virtual Fundraising</strong>
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
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'Treats Island <hasantechninja@gmail.com>')
        send_mail(
            subject=subject,
            message=text_content,
            from_email=from_email,
            recipient_list=[email],
            html_message=html_content,
            fail_silently=False,
        )
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send popup store created member email to {email}: {e}")


