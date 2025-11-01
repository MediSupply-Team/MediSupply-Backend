# ============================================================
# CLOUDFRONT DISTRIBUTIONS - HTTPS GRATIS
# ============================================================
# Proporciona HTTPS gratuito usando certificados de CloudFront
# para los BFFs públicos sin necesidad de dominio personalizado

# BFF VENTA - CloudFront Distribution
resource "aws_cloudfront_distribution" "bff_venta" {
  enabled         = true
  is_ipv6_enabled = true
  comment         = "BFF Venta - Free HTTPS via CloudFront"
  price_class     = "PriceClass_100"

  origin {
    domain_name = module.bff_venta.alb_dns_name
    origin_id   = "bff-venta-alb"

    custom_origin_config {
      http_port                = 80
      https_port               = 443
      origin_protocol_policy   = "http-only"
      origin_ssl_protocols     = ["TLSv1.2"]
      origin_keepalive_timeout = 5
      origin_read_timeout      = 30
    }
  }

  default_cache_behavior {
    target_origin_id       = "bff-venta-alb"
    viewer_protocol_policy = "redirect-to-https"

    allowed_methods = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods  = ["GET", "HEAD"]

    forwarded_values {
      query_string = true
      headers      = ["*"]

      cookies {
        forward = "all"
      }
    }

    min_ttl     = 0
    default_ttl = 0
    max_ttl     = 0

    compress = true
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
    minimum_protocol_version       = "TLSv1.2_2021"
  }

  tags = {
    Name    = "${var.project}-${var.env}-bff-venta-cloudfront"
    Project = var.project
    Env     = var.env
    Service = "bff-venta"
  }
}

# BFF CLIENTE - CloudFront Distribution
resource "aws_cloudfront_distribution" "bff_cliente" {
  enabled         = true
  is_ipv6_enabled = true
  comment         = "BFF Cliente - Free HTTPS via CloudFront"
  price_class     = "PriceClass_100"

  origin {
    domain_name = module.bff_cliente.alb_dns_name
    origin_id   = "bff-cliente-alb"

    custom_origin_config {
      http_port                = 80
      https_port               = 443
      origin_protocol_policy   = "http-only"
      origin_ssl_protocols     = ["TLSv1.2"]
      origin_keepalive_timeout = 5
      origin_read_timeout      = 30
    }
  }

  default_cache_behavior {
    target_origin_id       = "bff-cliente-alb"
    viewer_protocol_policy = "redirect-to-https"

    allowed_methods = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods  = ["GET", "HEAD"]

    forwarded_values {
      query_string = true
      headers      = ["*"]

      cookies {
        forward = "all"
      }
    }

    min_ttl     = 0
    default_ttl = 0
    max_ttl     = 0

    compress = true
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
    minimum_protocol_version       = "TLSv1.2_2021"
  }

  tags = {
    Name    = "${var.project}-${var.env}-bff-cliente-cloudfront"
    Project = var.project
    Env     = var.env
    Service = "bff-cliente"
  }
}

# ============================================================
# OUTPUTS - URLs HTTPS
# ============================================================

output "cloudfront_urls" {
  description = "URLs HTTPS de CloudFront (gratis)"
  value = {
    bff_venta = {
      https_url = "https://${aws_cloudfront_distribution.bff_venta.domain_name}"
      http_url  = "http://${module.bff_venta.alb_dns_name}"
      status    = aws_cloudfront_distribution.bff_venta.status
    }
    bff_cliente = {
      https_url = "https://${aws_cloudfront_distribution.bff_cliente.domain_name}"
      http_url  = "http://${module.bff_cliente.alb_dns_name}"
      status    = aws_cloudfront_distribution.bff_cliente.status
    }
  }
}

output "cloudfront_ids" {
  description = "IDs de las distribuciones de CloudFront"
  value = {
    bff_venta   = aws_cloudfront_distribution.bff_venta.id
    bff_cliente = aws_cloudfront_distribution.bff_cliente.id
  }
}
