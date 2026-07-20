<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:tei="http://www.tei-c.org/ns/1.0"
  xmlns:xml="http://www.w3.org/XML/1998/namespace">

  <xsl:output method="html" encoding="UTF-8" indent="yes" omit-xml-declaration="yes"/>
  <xsl:strip-space elements="*"/>
  <xsl:param name="assets_image_base">assets/images</xsl:param>
  <xsl:param name="assets_audio_base">assets/audio</xsl:param>
  <xsl:param name="assets_video_base">assets/video</xsl:param>

  <xsl:template match="/">
    <div class="tei-fragment">
      <xsl:apply-templates/>
    </div>
  </xsl:template>

  <!-- Ancre technique d'une note : son xml:id stable (jamais son @n, qui est
       un libellé éditorial potentiellement répété ou non conforme aux id HTML). -->
  <xsl:template name="note-anchor">
    <xsl:choose>
      <xsl:when test="normalize-space(@xml:id) != ''"><xsl:value-of select="@xml:id"/></xsl:when>
      <xsl:otherwise><xsl:value-of select="generate-id()"/></xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="tei:group | tei:text | tei:front | tei:body | tei:back">
    <xsl:apply-templates/>
    <xsl:if test="(self::tei:group or (self::tei:body and not(parent::*))) and .//tei:note">
      <section class="endnotes">
        <h2>Notes</h2>
        <ol>
          <xsl:for-each select=".//tei:note">
            <xsl:variable name="note-anchor">
              <xsl:call-template name="note-anchor"/>
            </xsl:variable>
            <li id="{$note-anchor}">
              <xsl:apply-templates select="node()"/>
              <xsl:text> </xsl:text>
              <a href="#noteref-{$note-anchor}">↩</a>
            </li>
          </xsl:for-each>
        </ol>
      </section>
    </xsl:if>
  </xsl:template>

  <xsl:template match="tei:titlePage">
    <section class="title-page"><xsl:apply-templates/></section>
  </xsl:template>

  <xsl:template match="tei:div">
    <section class="tei-div">
      <xsl:if test="@xml:id">
        <xsl:attribute name="id"><xsl:value-of select="@xml:id"/></xsl:attribute>
      </xsl:if>
      <xsl:if test="tei:head">
        <xsl:variable name="level" select="count(ancestor::tei:div) + 2"/>
        <xsl:choose>
          <xsl:when test="$level = 2"><h2><xsl:apply-templates select="tei:head[1]/node()"/></h2></xsl:when>
          <xsl:when test="$level = 3"><h3><xsl:apply-templates select="tei:head[1]/node()"/></h3></xsl:when>
          <xsl:otherwise><h4><xsl:apply-templates select="tei:head[1]/node()"/></h4></xsl:otherwise>
        </xsl:choose>
      </xsl:if>
      <xsl:apply-templates select="node()[not(self::tei:head)]"/>
    </section>
  </xsl:template>

  <xsl:template match="tei:head"/>

  <xsl:template match="tei:p">
    <p>
      <xsl:if test="@xml:id">
        <xsl:attribute name="id"><xsl:value-of select="@xml:id"/></xsl:attribute>
      </xsl:if>
      <xsl:apply-templates/>
    </p>
  </xsl:template>

  <xsl:template match="tei:cit">
    <div class="cit-block"><xsl:apply-templates/></div>
  </xsl:template>

  <xsl:template match="tei:p/tei:cit" priority="20">
    <span class="cit-inline"><xsl:apply-templates/></span>
  </xsl:template>

  <xsl:template match="tei:item/tei:cit" priority="20">
    <span class="cit-inline"><xsl:apply-templates/></span>
  </xsl:template>

  <xsl:template match="tei:note//tei:cit" priority="20">
    <span class="cit-inline"><xsl:apply-templates/></span>
  </xsl:template>

  <xsl:template match="tei:q">
    <q><xsl:apply-templates/></q>
  </xsl:template>

  <xsl:template match="tei:p/tei:quote" priority="20">
    <q><xsl:apply-templates/></q>
  </xsl:template>

  <xsl:template match="tei:p/tei:cit/tei:quote" priority="30">
    <q><xsl:apply-templates/></q>
  </xsl:template>

  <xsl:template match="tei:item/tei:cit/tei:quote" priority="30">
    <q><xsl:apply-templates/></q>
  </xsl:template>

  <xsl:template match="tei:note//tei:cit/tei:quote" priority="30">
    <q><xsl:apply-templates/></q>
  </xsl:template>

  <xsl:template match="tei:quote">
    <blockquote><xsl:apply-templates/></blockquote>
  </xsl:template>

  <xsl:template match="tei:table">
    <table>
      <xsl:apply-templates/>
    </table>
  </xsl:template>

  <xsl:template match="tei:table/tei:head" priority="20">
    <caption><xsl:apply-templates/></caption>
  </xsl:template>

  <xsl:template match="tei:row">
    <tr><xsl:apply-templates/></tr>
  </xsl:template>

  <xsl:template match="tei:cell">
    <xsl:choose>
      <xsl:when test="@role='label' or @role='header' or @type='head' or @type='header' or parent::tei:row[@role='label' or @role='header' or @type='head' or @type='header']">
        <th><xsl:apply-templates/></th>
      </xsl:when>
      <xsl:otherwise>
        <td><xsl:apply-templates/></td>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="tei:lg">
    <div class="poem-block"><xsl:apply-templates/></div>
  </xsl:template>

  <xsl:template match="tei:l">
    <div class="verse-line"><xsl:apply-templates/></div>
  </xsl:template>

  <xsl:template match="tei:epigraph">
    <blockquote class="epigraph"><xsl:apply-templates/></blockquote>
  </xsl:template>

  <xsl:template match="tei:figure">
    <figure>
      <xsl:if test="@xml:id">
        <xsl:attribute name="id"><xsl:value-of select="@xml:id"/></xsl:attribute>
      </xsl:if>
      <xsl:call-template name="render-figure-media"/>
      <xsl:if test="tei:head or tei:p">
        <figcaption>
          <xsl:if test="tei:head">
            <xsl:apply-templates select="tei:head[1]/node()"/>
          </xsl:if>
          <xsl:for-each select="tei:p">
            <div><xsl:apply-templates select="."/></div>
          </xsl:for-each>
        </figcaption>
      </xsl:if>
    </figure>
  </xsl:template>

  <xsl:template name="render-figure-media">
    <xsl:choose>
      <xsl:when test="tei:graphic[normalize-space(@url) != '']">
        <xsl:for-each select="tei:graphic[normalize-space(@url) != '']">
          <xsl:call-template name="render-graphic-image"/>
        </xsl:for-each>
      </xsl:when>
      <xsl:when test="tei:media[@url and starts-with(@mimeType, 'image/')]">
        <xsl:for-each select="tei:media[@url and starts-with(@mimeType, 'image/')]">
          <xsl:call-template name="render-media-image"/>
        </xsl:for-each>
      </xsl:when>
      <xsl:when test="tei:media[@url and starts-with(@mimeType, 'audio/')]">
        <audio controls="controls"><source><xsl:attribute name="src"><xsl:call-template name="resolved-audio-src"><xsl:with-param name="url" select="tei:media[1]/@url"/></xsl:call-template></xsl:attribute><xsl:attribute name="type"><xsl:value-of select="tei:media[1]/@mimeType"/></xsl:attribute></source></audio>
      </xsl:when>
      <xsl:when test="tei:media[@url and starts-with(@mimeType, 'video/')]">
        <video controls="controls"><source><xsl:attribute name="src"><xsl:call-template name="resolved-video-src"><xsl:with-param name="url" select="tei:media[1]/@url"/></xsl:call-template></xsl:attribute><xsl:attribute name="type"><xsl:value-of select="tei:media[1]/@mimeType"/></xsl:attribute></source></video>
      </xsl:when>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="render-graphic-image">
    <xsl:variable name="image-src"><xsl:call-template name="resolved-image-src"><xsl:with-param name="url" select="@url"/></xsl:call-template></xsl:variable>
    <xsl:variable name="image-alt">
      <xsl:choose>
        <xsl:when test="normalize-space(../tei:figDesc[1]) != ''"><xsl:value-of select="normalize-space(../tei:figDesc[1])"/></xsl:when>
        <xsl:otherwise><xsl:value-of select="normalize-space(../tei:head[1])"/></xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <button type="button" class="figure-zoom-trigger media-zoom-trigger" aria-label="Agrandir l'image">
      <xsl:attribute name="data-lightbox-src"><xsl:value-of select="$image-src"/></xsl:attribute>
      <xsl:if test="string-length($image-alt) &gt; 0">
        <xsl:attribute name="data-lightbox-alt"><xsl:value-of select="$image-alt"/></xsl:attribute>
        <xsl:attribute name="data-lightbox-caption"><xsl:value-of select="$image-alt"/></xsl:attribute>
      </xsl:if>
      <img>
        <xsl:attribute name="src"><xsl:value-of select="$image-src"/></xsl:attribute>
        <xsl:if test="string-length($image-alt) &gt; 0">
          <xsl:attribute name="alt"><xsl:value-of select="$image-alt"/></xsl:attribute>
        </xsl:if>
        <xsl:if test="normalize-space(@width) != ''">
          <xsl:attribute name="width"><xsl:value-of select="@width"/></xsl:attribute>
        </xsl:if>
        <xsl:if test="normalize-space(@height) != ''">
          <xsl:attribute name="height"><xsl:value-of select="@height"/></xsl:attribute>
        </xsl:if>
      </img>
    </button>
  </xsl:template>

  <xsl:template name="render-media-image">
    <xsl:variable name="image-src"><xsl:call-template name="resolved-image-src"><xsl:with-param name="url" select="@url"/></xsl:call-template></xsl:variable>
    <xsl:variable name="image-alt">
      <xsl:choose>
        <xsl:when test="normalize-space(../tei:figDesc[1]) != ''"><xsl:value-of select="normalize-space(../tei:figDesc[1])"/></xsl:when>
        <xsl:otherwise><xsl:value-of select="normalize-space(../tei:head[1])"/></xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <button type="button" class="figure-zoom-trigger media-zoom-trigger" aria-label="Agrandir l'image">
      <xsl:attribute name="data-lightbox-src"><xsl:value-of select="$image-src"/></xsl:attribute>
      <xsl:if test="string-length($image-alt) &gt; 0">
        <xsl:attribute name="data-lightbox-alt"><xsl:value-of select="$image-alt"/></xsl:attribute>
        <xsl:attribute name="data-lightbox-caption"><xsl:value-of select="$image-alt"/></xsl:attribute>
      </xsl:if>
      <img>
        <xsl:attribute name="src"><xsl:value-of select="$image-src"/></xsl:attribute>
        <xsl:if test="string-length($image-alt) &gt; 0">
          <xsl:attribute name="alt"><xsl:value-of select="$image-alt"/></xsl:attribute>
        </xsl:if>
      </img>
    </button>
  </xsl:template>

  <xsl:template name="resolved-image-src">
    <xsl:param name="url"/>
    <xsl:choose>
      <xsl:when test="contains($url, '://') or starts-with($url, '/') or starts-with($url, 'assets/') or starts-with($url, 'data:')"><xsl:value-of select="$url"/></xsl:when>
      <xsl:otherwise><xsl:value-of select="concat($assets_image_base, '/', $url)"/></xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="resolved-audio-src">
    <xsl:param name="url"/>
    <xsl:choose>
      <xsl:when test="contains($url, '://') or starts-with($url, '/') or starts-with($url, 'assets/')"><xsl:value-of select="$url"/></xsl:when>
      <xsl:otherwise><xsl:value-of select="concat($assets_audio_base, '/', $url)"/></xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="resolved-video-src">
    <xsl:param name="url"/>
    <xsl:choose>
      <xsl:when test="contains($url, '://') or starts-with($url, '/') or starts-with($url, 'assets/')"><xsl:value-of select="$url"/></xsl:when>
      <xsl:otherwise><xsl:value-of select="concat($assets_video_base, '/', $url)"/></xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="tei:note">
    <xsl:variable name="note-anchor">
      <xsl:call-template name="note-anchor"/>
    </xsl:variable>
    <sup class="note-ref" id="noteref-{$note-anchor}"><a href="#{$note-anchor}">
      <xsl:choose>
        <xsl:when test="normalize-space(@n) != ''"><xsl:value-of select="@n"/></xsl:when>
        <xsl:otherwise><xsl:number level="any" count="tei:note"/></xsl:otherwise>
      </xsl:choose>
    </a></sup>
  </xsl:template>

  <xsl:template match="tei:ref">
    <xsl:choose>
      <xsl:when test="@target">
        <a href="{@target}">
          <xsl:call-template name="external-link-attrs">
            <xsl:with-param name="target" select="@target"/>
          </xsl:call-template>
          <xsl:apply-templates/>
        </a>
      </xsl:when>
      <xsl:otherwise>
        <span class="tei-ref"><xsl:apply-templates/></span>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="tei:ptr">
    <xsl:choose>
      <xsl:when test="@target">
        <a class="tei-ptr" href="{@target}">
          <xsl:call-template name="external-link-attrs">
            <xsl:with-param name="target" select="@target"/>
          </xsl:call-template>
          <xsl:value-of select="@target"/>
        </a>
      </xsl:when>
      <xsl:otherwise>
        <span class="tei-ptr"></span>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="external-link-attrs">
    <xsl:param name="target"/>
    <xsl:if test="contains($target, '://')">
      <xsl:attribute name="target">_blank</xsl:attribute>
      <xsl:attribute name="rel">noopener</xsl:attribute>
    </xsl:if>
  </xsl:template>

  <xsl:template match="tei:title">
    <cite class="tei-title">
      <xsl:if test="@level">
        <xsl:attribute name="data-level"><xsl:value-of select="@level"/></xsl:attribute>
      </xsl:if>
      <xsl:if test="@type">
        <xsl:attribute name="data-type"><xsl:value-of select="@type"/></xsl:attribute>
      </xsl:if>
      <xsl:apply-templates/>
    </cite>
  </xsl:template>

  <xsl:template match="tei:bibl//tei:title" priority="30">
    <span class="tei-title">
      <xsl:if test="@level">
        <xsl:attribute name="data-level"><xsl:value-of select="@level"/></xsl:attribute>
      </xsl:if>
      <xsl:if test="@type">
        <xsl:attribute name="data-type"><xsl:value-of select="@type"/></xsl:attribute>
      </xsl:if>
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <xsl:template match="tei:foreign">
    <span class="foreign">
      <xsl:if test="@xml:lang">
        <xsl:attribute name="lang"><xsl:value-of select="@xml:lang"/></xsl:attribute>
      </xsl:if>
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <xsl:template match="tei:term">
    <span class="term">
      <xsl:call-template name="data-ref-attr"/>
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <xsl:template match="tei:name">
    <span class="name">
      <xsl:call-template name="data-ref-attr"/>
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <xsl:template match="tei:persName">
    <span class="pers-name">
      <xsl:call-template name="data-ref-attr"/>
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <xsl:template match="tei:placeName">
    <span class="place-name">
      <xsl:call-template name="data-ref-attr"/>
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <xsl:template match="tei:orgName">
    <span class="org-name">
      <xsl:call-template name="data-ref-attr"/>
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <xsl:template name="data-ref-attr">
    <xsl:if test="@ref">
      <xsl:attribute name="data-ref"><xsl:value-of select="@ref"/></xsl:attribute>
    </xsl:if>
  </xsl:template>

  <xsl:template match="tei:date">
    <time class="tei-date">
      <xsl:if test="@when">
        <xsl:attribute name="datetime"><xsl:value-of select="@when"/></xsl:attribute>
      </xsl:if>
      <xsl:apply-templates/>
    </time>
  </xsl:template>

  <xsl:template match="tei:num">
    <span class="tei-num">
      <xsl:if test="@type">
        <xsl:attribute name="data-type"><xsl:value-of select="@type"/></xsl:attribute>
      </xsl:if>
      <xsl:if test="@value">
        <xsl:attribute name="data-value"><xsl:value-of select="@value"/></xsl:attribute>
      </xsl:if>
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <xsl:template match="tei:label">
    <span class="tei-label"><xsl:apply-templates/></span>
  </xsl:template>

  <xsl:template match="tei:choice[tei:abbr and tei:expan]" priority="20">
    <abbr>
      <xsl:attribute name="title"><xsl:value-of select="normalize-space(tei:expan[1])"/></xsl:attribute>
      <xsl:apply-templates select="tei:abbr[1]/node()"/>
    </abbr>
  </xsl:template>

  <xsl:template match="tei:choice">
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="tei:abbr">
    <abbr><xsl:apply-templates/></abbr>
  </xsl:template>

  <xsl:template match="tei:expan">
    <span class="tei-expan"><xsl:apply-templates/></span>
  </xsl:template>

  <xsl:template match="tei:listBibl">
    <section class="tei-div bibliography-block">
      <xsl:if test="normalize-space(@xml:id) != ''">
        <xsl:attribute name="id"><xsl:value-of select="@xml:id"/></xsl:attribute>
      </xsl:if>
      <h2>Bibliographie</h2><ol class="bibl-list"><xsl:apply-templates/></ol>
    </section>
  </xsl:template>

  <xsl:template match="tei:listBibl/tei:bibl" priority="20">
    <li>
      <xsl:if test="normalize-space(@xml:id) != ''">
        <xsl:attribute name="id"><xsl:value-of select="@xml:id"/></xsl:attribute>
      </xsl:if>
      <xsl:apply-templates/>
    </li>
  </xsl:template>

  <xsl:template match="tei:listBibl/tei:biblStruct" priority="20">
    <li class="bibl-entry">
      <xsl:if test="normalize-space(@xml:id) != ''">
        <xsl:attribute name="id"><xsl:value-of select="@xml:id"/></xsl:attribute>
      </xsl:if>
      <xsl:apply-templates select="." mode="bibl-structured"/>
    </li>
  </xsl:template>

  <xsl:template match="tei:biblStruct">
    <span class="bibl-entry"><xsl:apply-templates/></span>
  </xsl:template>

  <xsl:template match="tei:biblStruct" mode="bibl-structured">
    <xsl:choose>
      <xsl:when test="tei:analytic">
        <span class="bibl-analytic"><xsl:apply-templates select="tei:analytic[1]" mode="bibl-structured"/></span>
        <xsl:if test="tei:monogr">
          <xsl:choose>
            <xsl:when test="tei:monogr[1]/tei:title[1][@level='j']">
              <xsl:text>, </xsl:text>
            </xsl:when>
            <xsl:otherwise>
              <xsl:text>, dans </xsl:text>
            </xsl:otherwise>
          </xsl:choose>
          <span class="bibl-monogr"><xsl:apply-templates select="tei:monogr[1]" mode="bibl-structured"/></span>
        </xsl:if>
      </xsl:when>
      <xsl:when test="tei:monogr">
        <span class="bibl-monogr"><xsl:apply-templates select="tei:monogr[1]" mode="bibl-structured"/></span>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates/>
      </xsl:otherwise>
    </xsl:choose>
    <xsl:text>.</xsl:text>
    <xsl:if test=".//tei:idno[normalize-space(.) != '']">
      <xsl:text> </xsl:text>
      <xsl:for-each select=".//tei:idno[normalize-space(.) != '']">
        <xsl:apply-templates select="." mode="bibl-structured"/>
        <xsl:text>.</xsl:text>
        <xsl:if test="position() != last()">
          <xsl:text> </xsl:text>
        </xsl:if>
      </xsl:for-each>
    </xsl:if>
  </xsl:template>

  <xsl:template match="tei:analytic" mode="bibl-structured">
    <xsl:if test="tei:author[normalize-space(.) != '']">
      <span class="bibl-author">
        <xsl:call-template name="render-bibl-name-list">
          <xsl:with-param name="nodes" select="tei:author[normalize-space(.) != '']"/>
        </xsl:call-template>
      </span>
      <xsl:if test="tei:title[normalize-space(.) != '']">
        <xsl:text>, </xsl:text>
      </xsl:if>
    </xsl:if>
    <xsl:if test="tei:title[normalize-space(.) != '']">
      <xsl:apply-templates select="tei:title[1]" mode="bibl-structured"/>
    </xsl:if>
  </xsl:template>

  <xsl:template match="tei:monogr" mode="bibl-structured">
    <xsl:if test="tei:author[normalize-space(.) != '']">
      <span class="bibl-author">
        <xsl:call-template name="render-bibl-name-list">
          <xsl:with-param name="nodes" select="tei:author[normalize-space(.) != '']"/>
        </xsl:call-template>
      </span>
      <xsl:if test="tei:title[normalize-space(.) != ''] or tei:imprint/*[normalize-space(.) != '']">
        <xsl:text>, </xsl:text>
      </xsl:if>
    </xsl:if>
    <xsl:if test="tei:editor[normalize-space(.) != '']">
      <span class="bibl-editor">
        <xsl:call-template name="render-bibl-name-list">
          <xsl:with-param name="nodes" select="tei:editor[normalize-space(.) != '']"/>
        </xsl:call-template>
      </span>
      <xsl:text> (dir.)</xsl:text>
      <xsl:if test="tei:title[normalize-space(.) != ''] or tei:imprint/*[normalize-space(.) != '']">
        <xsl:text>, </xsl:text>
      </xsl:if>
    </xsl:if>
    <xsl:if test="tei:title[normalize-space(.) != '']">
      <xsl:apply-templates select="tei:title[1]" mode="bibl-structured"/>
      <xsl:if test="tei:imprint/*[normalize-space(.) != '']">
        <xsl:text>, </xsl:text>
      </xsl:if>
    </xsl:if>
    <xsl:if test="tei:imprint/*[normalize-space(.) != '']">
      <span class="bibl-imprint"><xsl:apply-templates select="tei:imprint[1]" mode="bibl-structured"/></span>
    </xsl:if>
  </xsl:template>

  <xsl:template match="tei:imprint" mode="bibl-structured">
    <xsl:if test="tei:pubPlace[normalize-space(.) != '']">
      <xsl:apply-templates select="tei:pubPlace[1]" mode="bibl-structured"/>
    </xsl:if>
    <xsl:if test="tei:publisher[normalize-space(.) != '']">
      <xsl:if test="tei:pubPlace[normalize-space(.) != '']"><xsl:text>, </xsl:text></xsl:if>
      <xsl:apply-templates select="tei:publisher[1]" mode="bibl-structured"/>
    </xsl:if>
    <xsl:if test="tei:biblScope[@unit='volume' and normalize-space(.) != '']">
      <xsl:if test="tei:pubPlace[normalize-space(.) != ''] or tei:publisher[normalize-space(.) != '']"><xsl:text>, </xsl:text></xsl:if>
      <xsl:apply-templates select="tei:biblScope[@unit='volume'][1]" mode="bibl-structured"/>
    </xsl:if>
    <xsl:if test="tei:biblScope[@unit='issue' and normalize-space(.) != '']">
      <xsl:if test="tei:pubPlace[normalize-space(.) != ''] or tei:publisher[normalize-space(.) != ''] or tei:biblScope[@unit='volume' and normalize-space(.) != '']"><xsl:text>, </xsl:text></xsl:if>
      <xsl:text>no </xsl:text><xsl:apply-templates select="tei:biblScope[@unit='issue'][1]" mode="bibl-structured"/>
    </xsl:if>
    <xsl:if test="tei:date[normalize-space(.) != '']">
      <xsl:if test="tei:pubPlace[normalize-space(.) != ''] or tei:publisher[normalize-space(.) != ''] or tei:biblScope[(@unit='volume' or @unit='issue') and normalize-space(.) != '']"><xsl:text>, </xsl:text></xsl:if>
      <xsl:apply-templates select="tei:date[1]" mode="bibl-structured"/>
    </xsl:if>
    <xsl:if test="tei:biblScope[@unit='page' and normalize-space(.) != '']">
      <xsl:if test="tei:pubPlace[normalize-space(.) != ''] or tei:publisher[normalize-space(.) != ''] or tei:biblScope[(@unit='volume' or @unit='issue') and normalize-space(.) != ''] or tei:date[normalize-space(.) != '']"><xsl:text>, </xsl:text></xsl:if>
      <xsl:apply-templates select="tei:biblScope[@unit='page'][1]" mode="bibl-structured"/>
    </xsl:if>
    <xsl:for-each select="tei:biblScope[not(@unit='volume' or @unit='issue' or @unit='page') and normalize-space(.) != '']">
      <xsl:if test="../tei:pubPlace[normalize-space(.) != ''] or ../tei:publisher[normalize-space(.) != ''] or ../tei:biblScope[(@unit='volume' or @unit='issue' or @unit='page') and normalize-space(.) != ''] or ../tei:date[normalize-space(.) != ''] or position() &gt; 1"><xsl:text>, </xsl:text></xsl:if>
      <xsl:apply-templates select="." mode="bibl-structured"/>
    </xsl:for-each>
  </xsl:template>

  <xsl:template match="tei:biblStruct//tei:author">
    <span class="bibl-author"><xsl:apply-templates/></span>
  </xsl:template>

  <xsl:template match="tei:author" mode="bibl-structured">
    <span class="bibl-author"><xsl:apply-templates select="node()" mode="bibl-name"/></span>
  </xsl:template>

  <xsl:template match="tei:biblStruct//tei:editor">
    <span class="bibl-editor"><xsl:apply-templates/></span>
    <xsl:text> (dir.)</xsl:text>
  </xsl:template>

  <xsl:template match="tei:editor" mode="bibl-structured">
    <span class="bibl-editor"><xsl:apply-templates select="node()" mode="bibl-name"/></span>
    <xsl:text> (dir.)</xsl:text>
  </xsl:template>

  <xsl:template name="render-bibl-name-list">
    <xsl:param name="nodes"/>
    <xsl:for-each select="$nodes">
      <xsl:choose>
        <xsl:when test="position() = 1"/>
        <xsl:when test="position() = last()">
          <xsl:text> et </xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>, </xsl:text>
        </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="node()" mode="bibl-name"/>
    </xsl:for-each>
  </xsl:template>

  <xsl:template match="tei:persName" mode="bibl-name">
    <xsl:for-each select="node()[normalize-space(.) != '']">
      <xsl:if test="position() &gt; 1">
        <xsl:text> </xsl:text>
      </xsl:if>
      <xsl:apply-templates select="." mode="bibl-name"/>
    </xsl:for-each>
  </xsl:template>

  <xsl:template match="tei:forename | tei:surname" mode="bibl-name">
    <xsl:apply-templates select="node()" mode="bibl-name"/>
  </xsl:template>

  <xsl:template match="tei:biblStruct//tei:title" priority="40">
    <cite class="tei-title bibl-title">
      <xsl:if test="normalize-space(@level) != ''">
        <xsl:attribute name="data-level"><xsl:value-of select="@level"/></xsl:attribute>
      </xsl:if>
      <xsl:if test="normalize-space(@type) != ''">
        <xsl:attribute name="data-type"><xsl:value-of select="@type"/></xsl:attribute>
      </xsl:if>
      <xsl:apply-templates/>
    </cite>
  </xsl:template>

  <xsl:template match="tei:title" mode="bibl-structured">
    <xsl:choose>
      <xsl:when test="@level='a'">
        <xsl:choose>
          <xsl:when test="starts-with(normalize-space(.), '«') and substring(normalize-space(.), string-length(normalize-space(.)), 1) = '»'">
            <cite class="tei-title bibl-title">
              <xsl:if test="normalize-space(@level) != ''">
                <xsl:attribute name="data-level"><xsl:value-of select="@level"/></xsl:attribute>
              </xsl:if>
              <xsl:if test="normalize-space(@type) != ''">
                <xsl:attribute name="data-type"><xsl:value-of select="@type"/></xsl:attribute>
              </xsl:if>
              <xsl:apply-templates/>
            </cite>
          </xsl:when>
          <xsl:otherwise>
            <xsl:text>« </xsl:text>
            <cite class="tei-title bibl-title">
              <xsl:if test="normalize-space(@level) != ''">
                <xsl:attribute name="data-level"><xsl:value-of select="@level"/></xsl:attribute>
              </xsl:if>
              <xsl:if test="normalize-space(@type) != ''">
                <xsl:attribute name="data-type"><xsl:value-of select="@type"/></xsl:attribute>
              </xsl:if>
              <xsl:apply-templates/>
            </cite>
            <xsl:text> »</xsl:text>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:when>
      <xsl:otherwise>
        <cite class="tei-title bibl-title">
          <xsl:if test="normalize-space(@level) != ''">
            <xsl:attribute name="data-level"><xsl:value-of select="@level"/></xsl:attribute>
          </xsl:if>
          <xsl:if test="normalize-space(@type) != ''">
            <xsl:attribute name="data-type"><xsl:value-of select="@type"/></xsl:attribute>
          </xsl:if>
          <xsl:apply-templates/>
        </cite>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="tei:biblStruct//tei:pubPlace">
    <span class="bibl-pub-place"><xsl:apply-templates/></span>
  </xsl:template>

  <xsl:template match="tei:pubPlace" mode="bibl-structured">
    <span class="bibl-pub-place"><xsl:apply-templates/></span>
  </xsl:template>

  <xsl:template match="tei:biblStruct//tei:publisher">
    <span class="bibl-publisher"><xsl:apply-templates/></span>
  </xsl:template>

  <xsl:template match="tei:publisher" mode="bibl-structured">
    <span class="bibl-publisher"><xsl:apply-templates/></span>
  </xsl:template>

  <xsl:template match="tei:biblStruct//tei:date" priority="20">
    <time class="tei-date bibl-date">
      <xsl:if test="normalize-space(@when) != ''">
        <xsl:attribute name="datetime"><xsl:value-of select="@when"/></xsl:attribute>
      </xsl:if>
      <xsl:apply-templates/>
    </time>
  </xsl:template>

  <xsl:template match="tei:date" mode="bibl-structured">
    <time class="tei-date bibl-date">
      <xsl:if test="normalize-space(@when) != ''">
        <xsl:attribute name="datetime"><xsl:value-of select="@when"/></xsl:attribute>
      </xsl:if>
      <xsl:apply-templates/>
    </time>
  </xsl:template>

  <xsl:template match="tei:biblStruct//tei:biblScope">
    <span class="bibl-scope">
      <xsl:if test="normalize-space(@unit) != ''">
        <xsl:attribute name="data-unit"><xsl:value-of select="@unit"/></xsl:attribute>
      </xsl:if>
      <xsl:if test="normalize-space(@from) != ''">
        <xsl:attribute name="data-from"><xsl:value-of select="@from"/></xsl:attribute>
      </xsl:if>
      <xsl:if test="normalize-space(@to) != ''">
        <xsl:attribute name="data-to"><xsl:value-of select="@to"/></xsl:attribute>
      </xsl:if>
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <xsl:template match="tei:biblScope" mode="bibl-structured">
    <span class="bibl-scope">
      <xsl:if test="normalize-space(@unit) != ''">
        <xsl:attribute name="data-unit"><xsl:value-of select="@unit"/></xsl:attribute>
      </xsl:if>
      <xsl:if test="normalize-space(@from) != ''">
        <xsl:attribute name="data-from"><xsl:value-of select="@from"/></xsl:attribute>
      </xsl:if>
      <xsl:if test="normalize-space(@to) != ''">
        <xsl:attribute name="data-to"><xsl:value-of select="@to"/></xsl:attribute>
      </xsl:if>
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <xsl:template match="tei:biblStruct//tei:idno">
    <xsl:apply-templates select="." mode="bibl-structured"/>
  </xsl:template>

  <xsl:template match="tei:idno" mode="bibl-structured">
    <xsl:variable name="idno-value" select="normalize-space(.)"/>
    <xsl:if test="$idno-value != ''">
      <xsl:choose>
        <xsl:when test="@type='DOI'">
          <a class="bibl-idno" href="{concat('https://doi.org/', $idno-value)}" target="_blank" rel="noopener">
            <xsl:if test="normalize-space(@type) != ''">
              <xsl:attribute name="data-type"><xsl:value-of select="@type"/></xsl:attribute>
            </xsl:if>
            <xsl:text>DOI </xsl:text><xsl:value-of select="$idno-value"/>
          </a>
        </xsl:when>
        <xsl:when test="@type='URI' or @type='URL'">
          <a class="bibl-idno" href="{$idno-value}" target="_blank" rel="noopener">
            <xsl:if test="normalize-space(@type) != ''">
              <xsl:attribute name="data-type"><xsl:value-of select="@type"/></xsl:attribute>
            </xsl:if>
            <xsl:value-of select="@type"/><xsl:text> </xsl:text>
            <xsl:value-of select="$idno-value"/>
          </a>
        </xsl:when>
        <xsl:otherwise>
          <span class="bibl-idno">
            <xsl:if test="normalize-space(@type) != ''">
              <xsl:attribute name="data-type"><xsl:value-of select="@type"/></xsl:attribute>
              <xsl:value-of select="@type"/><xsl:text> </xsl:text>
            </xsl:if>
            <xsl:value-of select="$idno-value"/>
          </span>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:if>
  </xsl:template>

  <xsl:template match="tei:bibl">
    <cite class="bibl-ref"><xsl:apply-templates/></cite>
  </xsl:template>

  <xsl:template match="tei:list">
    <ul><xsl:apply-templates/></ul>
  </xsl:template>

  <xsl:template match="tei:item">
    <li><xsl:apply-templates/></li>
  </xsl:template>

    <!-- Typographie locale TEI / Métopes.
       normalize-space() permet de tolérer les espaces parasites,
       par exemple rend=" small-caps italic". -->

  <xsl:template match="tei:hi[contains(concat(' ', normalize-space(@rend), ' '), ' bold ') and contains(concat(' ', normalize-space(@rend), ' '), ' italic ')]" priority="30">
    <strong><em><xsl:apply-templates/></em></strong>
  </xsl:template>

  <xsl:template match="tei:hi[contains(concat(' ', normalize-space(@rend), ' '), ' small-caps ') and contains(concat(' ', normalize-space(@rend), ' '), ' italic ')] | tei:hi[normalize-space(@rend)='small-caps-ital']" priority="30">
    <span class="smallcaps"><em><xsl:apply-templates/></em></span>
  </xsl:template>

  <xsl:template match="tei:hi[contains(concat(' ', normalize-space(@rend), ' '), ' sup ') and contains(concat(' ', normalize-space(@rend), ' '), ' italic ')]" priority="30">
    <sup class="tei-sup"><em><xsl:apply-templates/></em></sup>
  </xsl:template>

  <xsl:template match="tei:hi[contains(concat(' ', normalize-space(@rend), ' '), ' italic ')] | tei:emph" priority="20">
    <em><xsl:apply-templates/></em>
  </xsl:template>

  <xsl:template match="tei:hi[contains(concat(' ', normalize-space(@rend), ' '), ' bold ')]" priority="20">
    <strong><xsl:apply-templates/></strong>
  </xsl:template>

  <xsl:template match="tei:hi[contains(concat(' ', normalize-space(@rend), ' '), ' small-caps ')] | tei:hi[normalize-space(@rend)='smallcaps']" priority="20">
    <span class="smallcaps"><xsl:apply-templates/></span>
  </xsl:template>

  <xsl:template match="tei:hi[contains(concat(' ', normalize-space(@rend), ' '), ' sup ')]" priority="20">
    <sup class="tei-sup"><xsl:apply-templates/></sup>
  </xsl:template>

  <xsl:template match="tei:hi[contains(concat(' ', normalize-space(@rend), ' '), ' sub ')]" priority="20">
    <sub class="tei-sub"><xsl:apply-templates/></sub>
  </xsl:template>

  <xsl:template match="tei:hi[contains(concat(' ', normalize-space(@rend), ' '), ' underline ')]" priority="20">
    <span class="tei-underline"><xsl:apply-templates/></span>
  </xsl:template>

  <xsl:template match="tei:hi[contains(concat(' ', normalize-space(@rend), ' '), ' strikethrough ')]" priority="20">
    <span class="tei-strikethrough"><xsl:apply-templates/></span>
  </xsl:template>

  <xsl:template match="tei:lb"><br/></xsl:template>

  <xsl:template match="tei:pb">
    <span class="page-break">
      <xsl:if test="@n">
        <xsl:attribute name="data-n"><xsl:value-of select="@n"/></xsl:attribute>
      </xsl:if>
      <xsl:if test="@n">
        <xsl:text>[p. </xsl:text>
        <xsl:value-of select="@n"/>
        <xsl:text>]</xsl:text>
      </xsl:if>
    </span>
  </xsl:template>

  <xsl:template match="text()"><xsl:value-of select="."/></xsl:template>
</xsl:stylesheet>
